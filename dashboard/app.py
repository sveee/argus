import json

import pandas as pd
from flask import Flask, render_template

from argus.tasks.base.database import TaskResult
from argus.tasks.base.serializable import JsonDict

app = Flask(__name__)


def get_task_latest_result(task_name: str) -> JsonDict:
    latest_task = (
        TaskResult.select()
        .where(TaskResult.task_id == task_name)
        .order_by(TaskResult.created_at.desc())
        .first()
    )
    return json.loads(latest_task.result)


def get_huggingface_models():
    models = get_task_latest_result('weekly_huggingface_models')
    models_df = pd.DataFrame(models['models'])
    models_df = models_df.sort_values('n_likes', ascending=False).head(10)
    models_df['url'] = 'https://huggingface.co/' + models_df['model_id']
    return models_df


def get_huggingface_papers():
    papers = get_task_latest_result('weekly_huggingface_papers')
    papers_df = pd.DataFrame(papers['papers'])
    papers_df = papers_df[['title', 'n_likes', 'url']]
    papers_df = papers_df.sort_values('n_likes', ascending=False).head(10)
    papers_df['url'] = 'https://huggingface.co' + papers_df['url']
    return papers_df


def get_papers_with_code():
    papers = get_task_latest_result('weekly_papers_with_code')
    papers_df = pd.DataFrame(papers['papers'])
    papers_df = papers_df.sort_values('stars_per_hour', ascending=False).head(10)
    return papers_df


def get_repos():
    repos = get_task_latest_result('weekly_github_ml_repos')
    repos_df = pd.DataFrame(repos['repos'])
    repos_df = repos_df.sort_values('n_recent_stars', ascending=False)
    repos_df.insert(
        0, 'repo', repos_df.url.apply(lambda x: x.removeprefix('https://github.com/'))
    )
    return repos_df


def get_date() -> str:
    latest_task = (
        TaskResult.select()
        .where(TaskResult.task_id == 'weekly_huggingface_models')
        .order_by(TaskResult.created_at.desc())
        .first()
    )
    return latest_task.created_at.strftime('%Y-%m-%d')


@app.route('/ml')
def ml_dashboard():
    return render_template(
        'ml.html',
        hf_papers=get_huggingface_papers(),
        hf_models=get_huggingface_models(),
        papers_with_code=get_papers_with_code(),
        gh_repos=get_repos(),
        date=get_date(),
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
