import streamlit as st

from argus.tasks.base.database import db, TaskResult
import pandas as pd
import json


def get_values(task_name: str) -> pd.DataFrame:
    with db:
        latest_task = (
            TaskResult
            .select()
            .where(TaskResult.task_name == task_name)
            .order_by(TaskResult.created_at.desc())
            .first()
        )

    return pd.DataFrame(json.loads(latest_task.result))


if __name__ == '__main__':
    st.set_page_config(layout='wide')
    models_tab, papers_tab = st.tabs(
        [
            'Models',
            'Papers',
        ]
    )
    HUGGING_FACE_DOMAIN = 'https://huggingface.co/'

    with models_tab:
        st.caption('Hugging Face')
        models = get_values('HuggingFaceTrendingModels').sort_values('n_likes', ascending=False)
        models['model_id'] = models.apply(lambda row: f'<a href="{HUGGING_FACE_DOMAIN + row["model_id"]}">{row["model_id"]}</a>', axis=1)
        st.write(models.to_html(escape=False, index=False), unsafe_allow_html=True)


    with papers_tab:
        st.caption('Hugging Face')
        papers = get_values('HuggingFaceTrendingPapers').sort_values('n_likes', ascending=False).iloc[:10]
        papers['title'] = papers.apply(lambda row: f'<a href="{HUGGING_FACE_DOMAIN + row["url"][1:]}">{row["title"]}</a>', axis=1)
        papers.drop(columns=['url'], inplace=True)
        st.write(papers.to_html(escape=False, index=False), unsafe_allow_html=True)

        st.caption('Papers With Code')
        papers = get_values('TrendingPapersWithCode').sort_values('stars_per_hour', ascending=False).iloc[:10]
        papers['title'] = papers.apply(lambda row: f'<a href="{row["url"]}">{row["title"]}</a>', axis=1)
        papers.drop(columns=['url'], inplace=True)
        st.write(papers.to_html(escape=False, index=False), unsafe_allow_html=True)

    # with github:
    #     posts = Formatted(
    #         TrendingGithubRepos({'Python', 'Jupyter Notebook'}),
    #         GithubStreamlitFormatter(),
    #     ).fetch_data()
    #     st.write(posts.to_html(escape=False, index=False), unsafe_allow_html=True)

    # with twitter:
    #     tweets = Formatted(MLRecentTweets(), TweetStreamlitFormatter()).fetch_data()
    #     st.write(tweets.to_html(escape=False, index=False), unsafe_allow_html=True)
