import json
from pathlib import Path

from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models.image import Image
from app.models.post import Post
from app.services.matching import (
    rank_images_for_post,
)
from app.services.recommendation import (
    recommend_images_for_post,
)


EVAL_PATH = Path("data/eval_posts.json")
RESULTS_PATH = Path("data/eval_results.json")


def load_eval_cases() -> list[dict]:
    with EVAL_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        cases = json.load(file)

    if len(cases) < 10:
        raise ValueError(
            "Evaluation dataset must contain "
            "at least 10 cases."
        )

    return cases


def main() -> None:
    cases = load_eval_cases()

    db = SessionLocal()

    results = []

    raw_correct = 0
    final_correct = 0
    no_match_count = 0

    try:
        print()
        print("=" * 70)
        print("IMAGE MATCHING EVALUATION")
        print("=" * 70)

        print(
            "Similarity threshold:",
            settings.match_similarity_threshold,
        )

        print(
            "Vision confidence threshold:",
            settings.vision_confidence_threshold,
        )

        print(
            "Evaluation cases:",
            len(cases),
        )

        print("=" * 70)
        print()

        for index, case in enumerate(
            cases,
            start=1,
        ):
            post = db.scalar(
                select(Post).where(
                    Post.title == case["title"],
                    Post.content == case["content"],
                )
            )

            if post is None:
                raise ValueError(
                    "Evaluation post not found: "
                    f"{case['case_id']}"
                )

            expected_image = db.scalar(
                select(Image).where(
                    Image.filename
                    == case["expected_image"]
                )
            )

            if expected_image is None:
                raise ValueError(
                    "Expected image not found: "
                    f"{case['expected_image']}"
                )

            ranked_images = (
                rank_images_for_post(
                    db=db,
                    post=post,
                    limit=50,
                )
            )

            if not ranked_images:
                raise ValueError(
                    "No ranked images returned for "
                    f"{case['case_id']}"
                )

            raw_top = ranked_images[0]

            raw_is_correct = (
                raw_top.filename
                == case["expected_image"]
            )

            if raw_is_correct:
                raw_correct += 1

            expected_rank = None
            expected_similarity = None

            for rank, candidate in enumerate(
                ranked_images,
                start=1,
            ):
                if (
                    candidate.filename
                    == case["expected_image"]
                ):
                    expected_rank = rank
                    expected_similarity = (
                        candidate.similarity
                    )
                    break

            recommendation_result = (
                recommend_images_for_post(
                    db=db,
                    post=post,
                    response_limit=10,
                )
            )

            recommendation = (
                recommendation_result.recommendation
            )

            if (
                not recommendation_result.match_found
                or recommendation is None
            ):
                predicted_image = None
                predicted_similarity = None
                final_is_correct = False
                no_match_count += 1

            else:
                predicted_image = (
                    recommendation.filename
                )

                predicted_similarity = (
                    recommendation.similarity
                )

                final_is_correct = (
                    predicted_image
                    == case["expected_image"]
                )

            if final_is_correct:
                final_correct += 1

            result = {
                "case_id": case["case_id"],
                "post_id": post.id,
                "title": post.title,
                "expected_image": (
                    case["expected_image"]
                ),
                "raw_top_image": (
                    raw_top.filename
                ),
                "raw_top_similarity": (
                    raw_top.similarity
                ),
                "raw_top_correct": (
                    raw_is_correct
                ),
                "expected_rank": expected_rank,
                "expected_similarity": (
                    expected_similarity
                ),
                "match_found": (
                    recommendation_result.match_found
                ),
                "predicted_image": (
                    predicted_image
                ),
                "predicted_similarity": (
                    predicted_similarity
                ),
                "final_correct": (
                    final_is_correct
                ),
                "message": (
                    recommendation_result.message
                ),
                "reasons": (
                    recommendation_result.reasons
                ),
            }

            results.append(result)

            status_text = (
                "PASS"
                if final_is_correct
                else "FAIL"
            )

            print(
                f"[{index}/{len(cases)}] "
                f"{case['case_id']}"
            )

            print(
                "Expected:",
                case["expected_image"],
            )

            print(
                "Raw Top-1:",
                raw_top.filename,
                f"({raw_top.similarity:.4f})",
            )

            print(
                "Expected Rank:",
                expected_rank,
            )

            if predicted_image is None:
                print(
                    "Final Recommendation:",
                    "NO CONFIDENT MATCH",
                )
            else:
                print(
                    "Final Recommendation:",
                    predicted_image,
                    f"({predicted_similarity:.4f})",
                )

            print(
                "Result:",
                status_text,
            )

            print("-" * 70)

    finally:
        db.close()

    total = len(cases)

    raw_precision = (
        raw_correct / total
        if total
        else 0
    )

    final_precision = (
        final_correct / total
        if total
        else 0
    )

    summary = {
        "total_cases": total,
        "raw_top1_correct": raw_correct,
        "raw_top1_precision": raw_precision,
        "final_top1_correct": final_correct,
        "final_top1_precision": final_precision,
        "no_confident_match_count": (
            no_match_count
        ),
        "similarity_threshold": (
            settings.match_similarity_threshold
        ),
        "vision_confidence_threshold": (
            settings.vision_confidence_threshold
        ),
    }

    output = {
        "summary": summary,
        "results": results,
    }

    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RESULTS_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
        )

    print()
    print("=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)

    print(
        f"Raw Ranking Top-1: "
        f"{raw_correct}/{total} "
        f"= {raw_precision:.2%}"
    )

    print(
        f"Final Recommendation Top-1: "
        f"{final_correct}/{total} "
        f"= {final_precision:.2%}"
    )

    print(
        "No Confident Match:",
        no_match_count,
    )

    print(
        "Similarity Threshold:",
        settings.match_similarity_threshold,
    )

    print(
        "Results saved to:",
        RESULTS_PATH,
    )

    print("=" * 70)


if __name__ == "__main__":
    main()
