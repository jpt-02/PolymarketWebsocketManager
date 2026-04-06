import logging
import logging.handlers
import queue
#from sub_script import perform_task

def console_logger():
    # use queue logging to reduce performance overhead
    # -1 argument is to indicate no bounds
    log_queue = queue.Queue(-1) 

    # Format and destination setup
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)

    # listener runs in background thread
    listener = logging.handlers.QueueListener(log_queue, console_handler)
    listener.start()

    # handler puts everything in the queue
    root = logging.getLogger()
    root.addHandler(logging.handlers.QueueHandler(log_queue))
    root.setLevel(logging.INFO)

    return listener

def setup_logging():
    # use queue logging to reduce performance overhead
    # -1 argument is to indicate no bounds
    log_queue = queue.Queue(-1) 

    # Format and destination setup
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)

    # listener runs in background thread
    listener = logging.handlers.QueueListener(log_queue, console_handler)
    listener.start()

    # handler puts everything in the queue
    root = logging.getLogger()
    root.addHandler(logging.handlers.QueueHandler(log_queue))
    root.setLevel(logging.INFO)

    return listener

if __name__ == "__main__":
    stop_event = setup_logging()
    
    logging.info("Master logging script started.")
    #perform_task()
    
    # Always stop the listener at the end of the program
    stop_event.stop()