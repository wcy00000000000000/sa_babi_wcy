# Created by WCY

"""templates_wcy.py: Templates for SA-bAbI code generation"""

FREE_LINES = ["free($ptr);"]

# templates for free in conditional / loop sentences

COND_DEC_INIT_PAIRS = [
    ("char* $ptr;", "$ptr = (char*) malloc($size);"),
    ("int $idx_var;", "$idx_var = $idx_init;"),
    ("int $thresh_var;", "$thresh_var = $thresh;")
]
COND_MAIN_LINES = [
    "if($idx_var < $thresh_var){",
    "   free($ptr);",
    "}",
]

WHILE_DEC_INIT_PAIRS = [
    ("char* $ptr;", "$ptr = (char*) malloc($size);"),
    ("int $idx_var;", "$idx_var = $idx_init;"),
    ("int $max_var;", "$max_var = $max_idx;")
]
WHILE_MAIN_LINES = [
    "while($idx_var < $max_var){",
    "   free($ptr);",
    "   $idx_var++;",
    "}",
]

FOR_DEC_INIT_PAIRS = [
    ("char* $ptr;", "$ptr = (char*) malloc($size);"),
    ("int $idx_var;", None),
    ("int $max_var;", "$max_var = $max_idx;")
]
FOR_MAIN_LINES = [
    "for($idx_var = $idx_init; $idx_var < $max_var; $idx_var++){",
    "   free($ptr);",
    "}"
]

# main function body wrapper

FUNC_TMPL_STR = """#include <stdlib.h>
int main()
{
$body
    return 0;
}"""
