# Created by WCY

"""sa_tag_wcy.py: defines the Tag class for SA-bAbI that detects CWE-415: Double Free"""
import enum


class Tag(enum.Enum):
    """Tags for each line of each instance representing pointer free safety

    e.g.
    void fun()                                               | OTHER
    {
        char* ptr = (char*)malloc (SIZE);                    | MALLOC
        if (abrt) {                                          | BODY
          free(ptr);                                         | FREE_TAUT_SAFE
        }                                                    | BODY
        free(ptr);                                           | FREE_COND_UNSAFE
    }                                                        | OTHER

    """
    # Function wrapping lines
    OTHER = 0
    # Lines inside body that aren't pointer free or malloc
    BODY = 1
    # Pointer free that requires control flow analysis to prove safe
    POINTER_FREE_COND_SAFE = 2
    # Pointer free that requires control flow analysis to prove unsafe
    POINTER_FREE_COND_UNSAFE = 3
    # Pointer free that is provably safe even without control flow
    POINTER_FREE_TAUT_SAFE = 4
    # Pointer free that is provably unsafe even without control flow
    POINTER_FREE_TAUT_UNSAFE = 5
