import time
import logging
import config


def github_event_stream(repos, req_types):
	logger = logging.getLogger("log")
	last_seen_ids = {}
	for repo in repos:
		last_seen_ids[repo.html_url] = int(repo.get_events()[0].id)
	logger.info("Starting event stream.")
	while True:
		for repo in repos:
			event_list = []
			for e in repo.get_events():
				event_list.append(e)
			event_list = [e for e in event_list if int(
				e.id) > last_seen_ids[repo.html_url]]
			event_list.sort(key=lambda e: int(e.id))
			if not event_list:
				logger.debug("No new events.")
			for e in event_list:
				if e.type in req_types:
					logger.debug("Yielding event.")
					yield repo, e
				last_seen_ids[repo.html_url] = int(e.id)
		logger.debug(f"Checking in {config.event_stream_wait}s.")
		time.sleep(config.event_stream_wait)
