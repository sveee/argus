import re
from typing import Optional

import pandas as pd
from tabulate import tabulate

emoji_pattern = re.compile(
    '['
    '\U0001f600-\U0001f64f'  # emoticons
    '\U0001f300-\U0001f5ff'  # symbols & pictographs
    '\U0001f680-\U0001f6ff'  # transport & map symbols
    '\U0001f1e0-\U0001f1ff'  # flags (iOS)
    '\U00002500-\U00002bef'  # chinese char
    '\U00002702-\U000027b0'
    '\U00002702-\U000027b0'
    '\U000024c2-\U0001f251'
    '\U0001f926-\U0001f937'
    '\U00010000-\U0010ffff'
    '\u2640-\u2642'
    '\u2600-\u2b55'
    '\u200d'
    '\u23cf'
    '\u23e9'
    '\u231a'
    '\ufe0f'  # dingbats
    '\u3030'
    ']+',
    re.UNICODE,
)


def normalize(text: str) -> str:
    text = emoji_pattern.sub(r'', text)
    return re.sub(r'\s+', ' ', text).strip()


def dataframe_to_str(
    data: pd.DataFrame,
    keep_columns: Optional[list[str]] = None,
    norm_columns: Optional[list[str]] = None,
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
