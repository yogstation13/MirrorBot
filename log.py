import logging

def make_logger(name):
	formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

	shandler = logging.StreamHandler()
	shandler.setFormatter(formatter)
	
	fhandler = logging.FileHandler("mirror.log")
	fhandler.setFormatter(formatter)

	logger = logging.getLogger(name)
	logger.setLevel(logging.DEBUG)
	logger.addHandler(shandler)
	logger.addHandler(fhandler)
	return logger