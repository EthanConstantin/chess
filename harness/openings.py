"""Curated opening suite for balanced rating matches.

A fixed set of 24 distinct, legal, mainstream opening lines (6-10 plies).
Each line is played twice with colors swapped to eliminate opening bias.
"""

OPENINGS: list[str] = [
    # 1. Ruy Lopez (8 plies)
    "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6",
    # 2. Italian Game (8 plies)
    "e2e4 e7e5 g1f3 b8c6 f1c4 f8c5 c2c3 g8f6",
    # 3. Four Knights (8 plies)
    "e2e4 e7e5 g1f3 b8c6 b1c3 g8f6 f1b5 f8b4",
    # 4. Scotch Game (8 plies)
    "e2e4 e7e5 g1f3 b8c6 d2d4 e5d4 f3d4 g8f6",
    # 5. Sicilian Najdorf (10 plies)
    "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 a7a6",
    # 6. Sicilian Dragon (10 plies)
    "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 g7g6",
    # 7. Sicilian Classical (10 plies)
    "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 b8c6",
    # 8. Sicilian Kan (8 plies)
    "e2e4 c7c5 g1f3 e7e6 d2d4 c5d4 f3d4 a7a6",
    # 9. French Winawer (6 plies)
    "e2e4 e7e6 d2d4 d7d5 b1c3 f8b4",
    # 10. French Classical (6 plies)
    "e2e4 e7e6 d2d4 d7d5 b1c3 g8f6",
    # 11. French Tarrasch (6 plies)
    "e2e4 e7e6 d2d4 d7d5 b1d2 g8f6",
    # 12. Caro-Kann Classical (8 plies)
    "e2e4 c7c6 d2d4 d7d5 b1c3 d5e4 c3e4 c8f5",
    # 13. Caro-Kann Advance (6 plies)
    "e2e4 c7c6 d2d4 d7d5 e4e5 c8f5",
    # 14. Queen's Gambit Declined (8 plies)
    "d2d4 d7d5 c2c4 e7e6 b1c3 g8f6 c1g5 f8e7",
    # 15. Slav Defense (8 plies)
    "d2d4 d7d5 c2c4 c7c6 g1f3 g8f6 b1c3 d5c4",
    # 16. King's Indian Defense (8 plies)
    "d2d4 g8f6 c2c4 g7g6 b1c3 f8g7 e2e4 d7d6",
    # 17. Nimzo-Indian Defense (6 plies)
    "d2d4 g8f6 c2c4 e7e6 b1c3 f8b4",
    # 18. Queen's Indian Defense (6 plies)
    "d2d4 g8f6 c2c4 e7e6 g1f3 b7b6",
    # 19. Grunfeld Defense (6 plies)
    "d2d4 g8f6 c2c4 g7g6 b1c3 d7d5",
    # 20. English Opening (6 plies)
    "c2c4 e7e5 b1c3 g8f6 g1f3 b8c6",
    # 21. London System (6 plies)
    "d2d4 d7d5 c1f4 g8f6 e2e3 c7c5",
    # 22. Scandinavian Defense (6 plies)
    "e2e4 d7d5 e4d5 d8d5 b1c3 d5a5",
    # 23. Pirc Defense (6 plies)
    "e2e4 d7d6 d2d4 g8f6 b1c3 g7g6",
    # 24. Vienna Game (6 plies)
    "e2e4 e7e5 b1c3 g8f6 f2f4 d7d5",
]
