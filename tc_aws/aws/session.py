import botocore.session
from botocore.utils import fix_s3_host

__all__ = ['get_session']

session = None

def get_session(custom_endpoint=False):
    '''
    Return a session object

    :param bool custom_endpoint: If true, prevent boto fiddling with the hostname
    :return Session: The session
    '''
    global session
    if session is None:
        session = botocore.session.get_session()
        if custom_endpoint:
            session.unregister('before-sign.s3', fix_s3_host)
    return session
