from app.services.matching import cosine_similarity


def main() -> None:
    identical = cosine_similarity(
        [1.0, 0.0],
        [1.0, 0.0],
    )

    orthogonal = cosine_similarity(
        [1.0, 0.0],
        [0.0, 1.0],
    )

    opposite = cosine_similarity(
        [1.0, 0.0],
        [-1.0, 0.0],
    )

    print(
        f"Identical: {identical}"
    )

    print(
        f"Orthogonal: {orthogonal}"
    )

    print(
        f"Opposite: {opposite}"
    )


if __name__ == "__main__":
    main()
