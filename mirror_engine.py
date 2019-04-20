import config
from github import Github
import sys
import mirror
import logging
import stream_events
import os
import subprocess
import pprint

class MirrorEngine:
	def __init__(self):
		self.github_api = None
		self.upstream = None
		self.downstream = None
		self.logger = logging.getLogger("log")
		
	def initialize(self):
		self.logger.info("Initializing mirror engine.")
		try:
			if config.username and config.password:
				self.github_api = Github(config.username, config.password)
			elif config.api_key:
				self.github_api = Github(config.api_key)
			else:
				self.logger.critical("No Github username/password or API key specified in config.")
				sys.exit()
		except Exception as e:
			self.logger.critical("Error while logging into Github, double-check credentials or try again later.")
			sys.exit()
			
		try:
			self.upstream = self.github_api.get_repo(f"{config.upstream_owner}/{config.upstream_repo}")
		except:
			self.logger.critical("Error while obtaining upstream repository info, check if owner and repo names were entered correctly.")
			sys.exit()
		
		try:
			self.downstream = self.github_api.get_repo(f"{config.downstream_owner}/{config.downstream_repo}")
		except:
			self.logger.critical("Error while obtaining upstream repository info, check if owner and repo names were entered correctly.")
			sys.exit()
		
		if not config.local_repo_directory:
			self.logger.critical("Local repo directory not set in config.")
			sys.exit()
			
		if os.path.isdir(config.local_repo_directory) and not os.path.isdir(f"{config.local_repo_directory}/.git"):
			self.logger.critical("Local repo directory already exists and is not a git repository.")
			sys.exit()

		if not os.path.isdir(config.local_repo_directory):
			self.logger.warning("Local clone of downstream repository not found, cloning.")
			try:
				subprocess.check_output(["git", "clone", f"https://github.com/{config.downstream_owner}/{config.downstream_repo}", f"{config.local_repo_directory}"])
				current_directory = os.getcwd()
				os.chdir(config.local_repo_directory)
				subprocess.check_output(["git", "remote", "add", "upstream", f"https://github.com/{config.upstream_owner}/{config.upstream_repo}"])
				subprocess.check_output(["git", "remote", "add", "downstream", f"https://github.com/{config.downstream_owner}/{config.downstream_repo}"])
				os.chdir(current_directory)
			except:
				self.logger.critical("An error occured during cloning.")
				sys.exit()
			
		self.logger.info("Mirror engine initialized successfully.")
		
	def run(self):
		self.logger.info("Mirror engine running.")
		for repo, event in stream_events.github_event_stream([self.upstream, self.downstream], ["PullRequestEvent", "IssueCommentEvent"]):
			if event.type == "PullRequestEvent" and repo == self.upstream:
				self.logger.debug("Processing PR event.")
				if event.payload["action"] == "closed" and event.payload["pull_request"]["merged"]:
					self.logger.info("Processing merge.")
					mirror.mirror_pr(self.upstream, self.downstream, int(event.payload["pull_request"]["number"]))
			elif event.type == "IssueCommentEvent" and repo == self.downstream:
				self.logger.debug("Processing comment.")
				if event.payload["action"] != "created": return
				self.logger.debug(f"User: {event.payload['comment']['user']['login']}")
				self.logger.debug(f"Contents: {event.payload['comment']['body']}")
				action = event.payload['comment']['body'].split()[0].lower()
				self.logger.debug(f"Action: {action}")
				if action.startswith("remirror"):
					if event.payload['comment']['author_association'] != "MEMBER" and event.payload['comment']['author_association'] != "OWNER":
						repo.get_comment(event.payload["comment"]["id"]).create_reaction("-1")
						return
					mirror.remirror_pr(self.upstream, self.downstream, event.payload["issue"]["number"])