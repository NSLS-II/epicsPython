import epicsMca

class hardwareMca(epicsMca.epicsMca):
    """
    This class is site-specific.  This version is for EPICS, and it simply
    inherits epicsMca.
    It must inherit from Mca, either directly or indirectly.
    In order to be used with mcaDisplay it must also implement the following
    methods that don't exist in Mca:
    erase()
    start()
    stop()
    get_acquire_status()
    new_acquire_status()
    new_elapsed()
    new_data()
    ...
    """
    def __init__(self, *args, **kw):
       epicsMca.epicsMca.__init__(self, *args, **kw)
