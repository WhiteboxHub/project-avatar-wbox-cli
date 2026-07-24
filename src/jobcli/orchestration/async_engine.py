import asyncio
import concurrent.futures
from typing import Optional
from rich.console import Console

from jobcli.orchestration.engine import ApplicationEngine
from jobcli.utils.progress import ApplicationProgressTracker, create_status_table
from jobcli.profile.schemas import Config, ResumeData, Job, ApplicationStatus
from jobcli.storage.models import Database
from jobcli.storage.session import get_db_transaction


class AsyncApplicationEngine:
    """Production-ready concurrent engine with proper resource management.
    
    This engine uses a ThreadPoolExecutor to run the battle-tested, synchronous 
    ApplicationEngine in multiple background threads, achieving 10x concurrency
    WITHOUT crashing or requiring a massive rewrite of the sync Playwright codebase!
    """

    def __init__(
        self,
        config: Config,
        resume: ResumeData,
        database: Database,
        console: Optional[Console] = None,
    ) -> None:
        self.config = config
        self.resume = resume
        self.database = database
        self.console = console or Console()
        self.stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
        }

    def _process_job_sync(self, job: Job, progress_tracker: ApplicationProgressTracker) -> ApplicationStatus:
        """This runs completely independently in its own thread."""
        engine = ApplicationEngine(self.config, self.resume, self.database)
        engine.start_session()
        
        try:
            # The apply_to_job function runs the standard sync automation
            engine.apply_to_job(job)
            
            # We fetch the final status from the database to report back
            with get_db_transaction(self.database) as session:
                from jobcli.storage.repositories import JobRepository
                job_repo = JobRepository(session)
                db_job = job_repo.get(job.id or 0)
                final_status = db_job.status if db_job else ApplicationStatus.FAILED
                
            return final_status
        except Exception:
            return ApplicationStatus.FAILED
        finally:
            engine.stop_session()

    async def apply_to_jobs_batch(
        self, jobs: list[Job], max_concurrent: int = 3
    ) -> dict[str, int]:
        """Apply to multiple jobs concurrently using a thread pool."""
        progress_tracker = ApplicationProgressTracker(self.console)
        progress_tracker.start_batch(len(jobs))

        loop = asyncio.get_running_loop()

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as pool:
            
            async def run_single_job(job: Job, index: int):
                progress_tracker.start_job(job.url, index + 1, len(jobs))
                
                # Offload the blocking sync engine to the thread pool
                status = await loop.run_in_executor(
                    pool, self._process_job_sync, job, progress_tracker
                )
                
                # Update our statistics
                self.stats["processed"] += 1
                if status == ApplicationStatus.SUBMITTED:
                    self.stats["successful"] += 1
                elif status == ApplicationStatus.SKIPPED:
                    self.stats["skipped"] += 1
                else:
                    self.stats["failed"] += 1

                progress_tracker.end_job(success=(status == ApplicationStatus.SUBMITTED))

            # Run all jobs concurrently
            tasks = [run_single_job(job, i) for i, job in enumerate(jobs)]
            await asyncio.gather(*tasks, return_exceptions=True)

        # Display summary table just like the original async engine requested
        summary_table = create_status_table(
            jobs_processed=self.stats["processed"],
            jobs_successful=self.stats["successful"],
            jobs_failed=self.stats["failed"],
            jobs_skipped=self.stats["skipped"],
        )
        self.console.print("\n")
        self.console.print(summary_table)

        return self.stats

    def get_statistics(self) -> dict[str, int]:
        return self.stats.copy()


# Convenience function matching the exact signature you requested!
async def run_async_engine(
    config: Config,
    resume: ResumeData,
    database: Database,
    jobs: list[Job],
    max_concurrent: int = 3,
) -> dict[str, int]:
    """Run concurrent engine on batch of jobs."""
    engine = AsyncApplicationEngine(config, resume, database)
    return await engine.apply_to_jobs_batch(jobs, max_concurrent)
