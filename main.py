import mirror_engine
import log
logger = log.make_logger("log")
logger.info("Starting.")

while True:
	engine = mirror_engine.MirrorEngine()
	engine.initialize()
	try:
		engine.run()
	except:
		logger.exception("Uncaught exception!")

# TODO:
# compare diffs on up and downstream
# update downstream dme with upstream
