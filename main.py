import log
logger = log.make_logger("log")
logger.info("Starting.")

import mirror_engine

engine = mirror_engine.MirrorEngine()
engine.initialize()
engine.run()

#TODO:
# compare diffs on up and downstream
# update downstream dme with upstream