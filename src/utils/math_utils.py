from typing import TypeVar

T = TypeVar("T")


def clamp(value: T, min_value: T, max_value: T) -> T:
    """
    주어진 값(value)을 최소값(min_value)과 최대값(max_value) 사이로 조정합니다.

    Parameters:
        value (T): 조정할 값
        min_value (T): 최소값
        max_value (T): 최대값

    Returns:
        T: 조정된 값
    """
    return max(min(value, max_value), min_value)


def lerp(a: T, b: T, alpha: float) -> float:
    """
    선형 보간법을 사용하여 a와 b 사이에서 alpha 비율에 따라 값을 보간합니다.

    Parameters:
        a (T): 보간의 시작 값
        b (T): 보간의 끝 값
        alpha (float): 보간 비율 (0과 1 사이의 값)

    Returns:
        T: 보간된 값
    """
    return a + (b - a) * alpha
