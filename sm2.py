import math

def calculate_next_review(quality: int, repetition: int, ef: float, interval: int) -> tuple[int, float, int]:
    """
    Calculates the next review intervals using a simplified SM-2 algorithm.
    """
    if not (0 <= quality <= 5):
        raise ValueError("Quality score must be between 0 and 5.")

    if quality >= 3:
        # Correct response
        if repetition == 0:
            new_interval = 1
        elif repetition == 1:
            new_interval = 6
        else:
            # Multiply old interval by the EF and round up
            new_interval = math.ceil(interval * ef)
        
        # Calculate new_ef
        new_ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        
        # Ensure new_ef is never less than 1.3
        new_ef = max(1.3, new_ef)
        
        new_repetition = repetition + 1

    else:
        # Incorrect response
        new_repetition = 0
        new_interval = 1
        new_ef = ef # EF does not change on failure

    return new_repetition, new_ef, new_interval

# --- Terminal Test Block ---
if __name__ == "__main__":
    print("Testing SM-2 Logic:")
    
    # Simulate a new card (N=0, EF=2.5, I=0) getting a perfect score (5)
    n, ef, i = calculate_next_review(quality=5, repetition=0, ef=2.5, interval=0)
    print(f"Test 1 (New Card, Score 5): Repetition={n}, EF={ef:.2f}, Interval={i} days")
    
    # Simulate an established card getting a bad score (1)
    n2, ef2, i2 = calculate_next_review(quality=1, repetition=4, ef=2.6, interval=12)
    print(f"Test 2 (Old Card, Score 1): Repetition={n2}, EF={ef2:.2f}, Interval={i2} days")