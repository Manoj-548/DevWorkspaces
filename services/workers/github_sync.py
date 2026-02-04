"""GitHub Sync Worker - Continuously monitors GitHub repositories"""

import asyncio
import requests
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

import sys
sys.path.insert(0, '/home/manoj/DevWorkspaces')

from services.database import db
from services.websocket_manager import manager
from services.config import WORKER_INTERVALS, CHANNELS, GITHUB_CONFIG

logger = logging.getLogger(__name__)


class GitHubSyncWorker:
    """Continuously monitors GitHub repositories"""
    
    def __init__(self):
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self.last_workflows = []
        self.last_status = {}
    
    async def start(self, interval: int = None):
        """Start the GitHub sync worker"""
        interval = interval or WORKER_INTERVALS["github_sync"]
        self.running = True
        self._task = asyncio.create_task(self._run(interval))
        logger.info(f"GitHub sync worker started with interval {interval}s")
    
    async def stop(self):
        """Stop the GitHub sync worker"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("GitHub sync worker stopped")
    
    async def _run(self, interval: int):
        """Main sync loop"""
        while self.running:
            try:
                # Fetch repository status
                status = await self._fetch_repo_status()
                if status:
                    await self._process_status(status)
                
                # Fetch workflows
                workflows = await self._fetch_workflows()
                if workflows:
                    await self._process_workflows(workflows)
                
            except Exception as e:
                logger.error(f"GitHub sync error: {e}")
                await db.save_log(
                    source="github_sync",
                    level="error",
                    message=f"Sync error: {str(e)}"
                )
            
            await asyncio.sleep(interval)
    
    async def _get_headers(self) -> Dict[str, str]:
        """Get headers for GitHub API"""
        headers = {"Accept": "application/vnd.github.v3+json"}
        github_token = os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
        if github_token:
            headers["Authorization"] = f"token {github_token}"
        return headers
    
    async def _fetch_repo_status(self) -> Optional[Dict[str, Any]]:
        """Fetch repository status"""
        github_repo = "Manoj-548/DevWorkspaces"
        
        try:
            response = requests.get(
                f"{GITHUB_CONFIG['api_url']}/repos/{github_repo}",
                headers=await self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "name": data.get("name"),
                    "full_name": data.get("full_name"),
                    "stars": data.get("stargazers_count", 0),
                    "forks": data.get("forks_count", 0),
                    "open_issues": data.get("open_issues_count", 0),
                    "description": data.get("description"),
                    "language": data.get("language"),
                    "default_branch": data.get("default_branch"),
                    "last_updated": data.get("updated_at"),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.warning(f"GitHub API returned {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching repo status: {e}")
            return None
    
    async def _fetch_workflows(self) -> Optional[List[Dict]]:
        """Fetch GitHub Actions workflows"""
        github_repo = "Manoj-548/DevWorkspaces"
        
        try:
            response = requests.get(
                f"{GITHUB_CONFIG['api_url']}/repos/{github_repo}/actions/runs",
                headers=await self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("workflow_runs", [])
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error fetching workflows: {e}")
            return None
    
    async def _process_status(self, status: Dict[str, Any]):
        """Process repository status"""
        # Check for changes
        if status != self.last_status:
            # Broadcast to subscribers
            await manager.broadcast(CHANNELS["github_events"], {
                "type": "repo_status",
                **status
            })
            
            # Save to database
            await db.save_event(
                event_type="github_status",
                event_id=f"status_{status['full_name']}_{status['timestamp']}",
                data=status,
                channel="github"
            )
            
            # Log significant changes
            if self.last_status:
                changes = []
                if status["stars"] != self.last_status.get("stars"):
                    changes.append(f"Stars: {self.last_status.get('stars')} -> {status['stars']}")
                if status["open_issues"] != self.last_status.get("open_issues"):
                    changes.append(f"Issues: {self.last_status.get('open_issues')} -> {status['open_issues']}")
                
                if changes:
                    await db.save_log(
                        source="github_sync",
                        level="info",
                        message=f"Repository updated: {', '.join(changes)}",
                        metadata=status
                    )
            
            self.last_status = status
    
    async def _process_workflows(self, workflows: List[Dict]):
        """Process workflow runs"""
        # Check for new/failed workflows
        for workflow in workflows[:10]:  # Process last 10
            run_id = str(workflow.get("id"))
            
            # Check if we already have this workflow
            is_new = await db.check_duplicate("workflow", run_id)
            
            if not is_new:
                continue
            
            # Mark as seen
            await db.mark_seen("workflow", run_id)
            
            # Save event
            event_data = {
                "name": workflow.get("name"),
                "status": workflow.get("status"),
                "conclusion": workflow.get("conclusion"),
                "branch": workflow.get("head_branch"),
                "event": workflow.get("event"),
                "run_id": run_id,
                "timestamp": workflow.get("created_at"),
                "updated_at": workflow.get("updated_at")
            }
            
            await db.save_event(
                event_type="workflow",
                event_id=run_id,
                data=event_data,
                channel="github"
            )
            
            # Broadcast based on conclusion
            if workflow.get("conclusion") == "failure":
                await manager.broadcast(CHANNELS["github_events"], {
                    "type": "workflow_failed",
                    **event_data
                })
                
                await db.save_log(
                    source="github_actions",
                    level="error",
                    message=f"Workflow failed: {workflow.get('name')} on {workflow.get('head_branch')}",
                    metadata=event_data
                )
            elif workflow.get("conclusion") == "success":
                await manager.broadcast(CHANNELS["github_events"], {
                    "type": "workflow_success",
                    **event_data
                })
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            "running": self.running,
            "last_status": self.last_status,
            "last_workflow_count": len(self.last_workflows)
        }


# Global instance
github_sync_worker = GitHubSyncWorker()

