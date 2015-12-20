from croniter import croniter
import datetime
import logging

log = logging.getLogger("python_dashing.scheduler")

class Scheduler(object):
    def __init__(self):
        self.check_times = {}
        self.checks = []

    def register(self, module, server, module_name):
        for cron, func in server.register_checks:
            self.checks.append((cron, func, module, module_name))

    def run(self, datastore, force=False):
        now = datetime.datetime.now()
        for cron, func, module, module_name in self.checks:
            key = "{0}_{1}".format(cron.replace(" ", "_").replace("/", "SLSH").replace("*", "STR"), func.__name__)
            iterable = croniter(cron, self.check_times.get(key, now))
            nxt = iterable.get_next(datetime.datetime)
            if not force:
                if nxt > now and key in self.check_times:
                    continue

            log.info("Triggering cron: {0}.{1} '{2}'".format(module_name, func.__name__, cron))
            try:
                ds = datastore.prefixed("{0}-{1}".format(module.relative_to, module_name))
                for key, value in func(now - self.check_times.get(key, now)):
                    ds.create(key, value)
            except Exception:
                log.exception("Error running a check\tmodule={0}\tcheck={1}".format(module_name, func.__name__))
            finally:
                self.check_times[key] = now
