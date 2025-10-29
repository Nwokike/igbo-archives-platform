def get_form():
    """Official hook for threadedcomments to get custom form"""
    from core.forms import CaptchaThreadedCommentForm
    return CaptchaThreadedCommentForm
