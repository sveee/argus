import re
from typing import List, Optional

import pandas as pd
from tabulate import tabulate

emoji_pattern = re.compile(
    "["
    u"\U0001F600-\U0001F64F"  # emoticons
    u"\U0001F300-\U0001F5FF"  # symbols & pictographs
    u"\U0001F680-\U0001F6FF"  # transport & map symbols
    u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
    u"\U00002500-\U00002BEF"  # chinese char
    u"\U00002702-\U000027B0"
    u"\U00002702-\U000027B0"
    u"\U000024C2-\U0001F251"
    u"\U0001f926-\U0001f937"
    u"\U00010000-\U0010ffff"
    u"\u2640-\u2642"
    u"\u2600-\u2B55"
    u"\u200d"
    u"\u23cf"
    u"\u23e9"
    u"\u231a"
    u"\ufe0f"  # dingbats
    u"\u3030"
    "]+",
    re.UNICODE,
)


def normalize(text: str) -> str:
    text = emoji_pattern.sub(r'', text)
    return re.sub(r'\s+', ' ', text).strip()


def dataframe_to_str(
    data: pd.DataFrame,
    keep_columns: Optional[List[str]] = None,
    norm_columns: Optional[List[str]] = None,
    max_col_width: Optional[int] = None,
    show_index: bool = False,
) -> str:
    if norm_columns:
        for column in norm_columns:
            data[column] = data[column].apply(normalize)
    return tabulate(
        data[keep_columns] if keep_columns is not None else data,
        headers='keys',
        tablefmt='psql',
        showindex=show_index,
        maxcolwidths=max_col_width,
        floatfmt='.2f',
    )
