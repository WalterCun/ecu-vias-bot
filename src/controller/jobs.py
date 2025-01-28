from telegram.ext import ContextTypes


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Remove a job if it exists in the given context.

    :param name: The name of the job.
    :param context: The context to search for the job.

    :return: True if the job was found and successfully removed, False otherwise.
    """
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True
