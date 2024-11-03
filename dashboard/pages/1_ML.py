import json

import pandas as pd
import streamlit as st

from argus.tasks.base.database import TaskResult, db


def get_values(task_name: str) -> pd.DataFrame:
    with db:
        latest_task = (
            TaskResult.select()
            .where(TaskResult.task_name == task_name)
            .order_by(TaskResult.created_at.desc())
            .first()
        )

    return pd.DataFrame(json.loads(latest_task.result))


if __name__ == '__main__':
    st.set_page_config(layout='wide')

    HUGGING_FACE_DOMAIN = 'https://huggingface.co/'

    st.caption('Hugging Face Models')
    models = get_values('HuggingFaceTrendingModels').sort_values(
        'n_likes', ascending=False
    )
    models['model_id'] = models.apply(
        lambda row: f'<a href="{HUGGING_FACE_DOMAIN + row["model_id"]}">{row["model_id"]}</a>',
        axis=1,
    )
    st.write(models.to_html(escape=False, index=False), unsafe_allow_html=True)

    st.caption('Hugging Face Papers')
    papers = (
        get_values('HuggingFaceTrendingPapers')
        .sort_values('n_likes', ascending=False)
        .iloc[:10]
    )
    papers['title'] = papers.apply(
        lambda row: f'<a href="{HUGGING_FACE_DOMAIN + row["url"][1:]}">{row["title"]}</a>',
        axis=1,
    )
    papers.drop(columns=['url'], inplace=True)
    st.write(papers.to_html(escape=False, index=False), unsafe_allow_html=True)

    st.caption('Papers With Code')
    papers = (
        get_values('TrendingPapersWithCode')
        .sort_values('stars_per_hour', ascending=False)
        .iloc[:10]
    )
    papers['title'] = papers.apply(
        lambda row: f'<a href="{row["url"]}">{row["title"]}</a>', axis=1
    )
    papers.drop(columns=['url'], inplace=True)
    st.write(papers.to_html(escape=False, index=False), unsafe_allow_html=True)

    st.caption('Github Repos')
    repos = get_values('TrendingGithubRepos').sort_values(
        'n_recent_stars', ascending=False
    )
    repos['description'] = repos['description'].apply(lambda s: s.strip())
    repos.insert(
        0,
        'repo',
        repos.url.apply(
            lambda url: f'<a href="{url}">{url.lstrip("https://github.com/")}</a>'
        ),
    )
    repos.drop(columns=['n_recent_stars', 'url'], inplace=True)
    st.write(repos.to_html(escape=False, index=False), unsafe_allow_html=True)
