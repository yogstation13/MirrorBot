import os
import logging
import subprocess
import config
import sys


def clean_repo():
	logger = logging.getLogger("log")
	logger.debug("Cleaning local repo.")
	subprocess.run(["git", "fetch", "--all"],
	               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	subprocess.run(["git", "checkout", "master"],
	               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	subprocess.run(["git", "reset", "--hard", "downstream/master"],
	               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	subprocess.run(["git", "clean", "-f"],
	               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	logger.debug("Deleting branches.")
	for deletable_branch in [line.strip().decode() for line in subprocess.check_output(["git", "branch"]).splitlines() if line != b"* master"]:
		subprocess.run(["git", "branch", "-D", deletable_branch],
		               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def mirror_pr(upstream, downstream, pr_id):
	logger = logging.getLogger("log")
	logger.info(f"Mirroring PR #{pr_id}.")
	current_directory = os.getcwd()
	try:
		os.chdir(config.local_repo_directory)
		original_pull = upstream.get_pull(pr_id)
		clean_repo()
		logger.debug("Switching to mirror branch.")
		subprocess.run(["git", "checkout", "-b", f"{config.mirror_branch_prefix}{pr_id}"],
		               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

		try:
			logger.debug("Cherry-picking merge commit.")
			cherry_out = subprocess.check_output(["git", "cherry-pick", "-m", "1",
                                         original_pull.merge_commit_sha], stderr=subprocess.STDOUT)
		except subprocess.CalledProcessError as e:
			cherry_out = str(e.output)

		try:
			cherry_out = cherry_out.decode()  # love python3
		except:
			pass

		if "mainline was specified but commit" in cherry_out:
			logger.info("PR was merged via squash.")
			commits = original_pull.get_commits()
			subprocess.run(["git", "fetch", "--all"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			if original_pull.merge_commit_sha in [c.sha for c in commits]:
				for c in commits:
					subprocess.run(["git", "cherry-pick", "--no-commit", "-n", c.sha])
					subprocess.run(["git", "add", "-A", "."])
					subprocess.run(["git", "commit", "--no-edit", "-m", c.commit.message])
					subprocess.run(["git", "cherry-pick", "--continue"])
			else:
				subprocess.run(["git", "cherry-pick", "--no-commit", "-n",
                                    original_pull.merge_commit_sha])
				subprocess.run(["git", "add", "-A", "."])
				subprocess.run(["git", "commit", "--no-edit", "-m", original_pull.title])
				subprocess.run(["git", "cherry-pick", "--continue"])
		else:
			subprocess.run(["git", "add", "-A", "."])

		subprocess.run(["git", "commit", "--allow-empty", "--no-edit", "-m", original_pull.title],
		               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		logger.debug("Pushing to downstream.")
		subprocess.run(["git", "push", "downstream",
                  f"{config.mirror_branch_prefix}{pr_id}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

		logger.info("Creating pull request.")
		result = downstream._Repository__create_pull(title=f"{config.mirror_pr_title_prefix}{original_pull.title}",
                                               body=f"Original PR: {original_pull.html_url}\n-----\n{original_pull.body}",
                                               base="master",
                                               head=f"{config.mirror_branch_prefix}{pr_id}",
                                               maintainer_can_modify=True)

		logger.info(f"Pull request created: {result.title} (#{result.number})")
		return result
	except:
		logger.exception("An error occured during mirroring.")
	finally:
		os.chdir(current_directory)


def remirror_pr(upstream, downstream, mirror_pr_id):
	logger = logging.getLogger("log")
	logger.info(f"Remirroring #{mirror_pr_id}.")
	current_directory = os.getcwd()
	try:
		os.chdir(config.local_repo_directory)
		mirror_pull = downstream.get_pull(mirror_pr_id)
		# Get original PR number from the "Original PR: " link
		original_pull = upstream.get_pull(
			int(mirror_pull.body.split("/")[6].split("\n")[0]))
		clean_repo()
		logger.debug("Switching to mirror branch.")
		subprocess.run(["git", "checkout", "-b", f"{config.mirror_branch_prefix}{original_pull.number}"],
		               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		logger.debug("Cherry-picking merge commit.")
		subprocess.run(["git", "cherry-pick", "-m", "1", original_pull.merge_commit_sha],
		               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		logger.debug("Force pushing to downstream.")
		subprocess.run(["git", "push", "--force", "downstream",
                  f"{config.mirror_branch_prefix}{original_pull.number}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	except:
		logger.exception("An error occured during remirroring.")
	finally:
		os.chdir(current_directory)
