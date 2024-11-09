from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import get_template

from django_rest_passwordreset.signals import reset_password_token_created


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    print("I got called!")
    """
    Handles password reset tokens
    When a token is created, an e-mail needs to be sent to the user
    :param sender: View Class that sent the signal
    :param instance: View Instance that sent the signal
    :param reset_password_token: Token Model Object
    :param args:
    :param kwargs:
    :return:
    """
    # send an e-mail to the user
    context = {
        'current_user': reset_password_token.user,
        'username': reset_password_token.user.username,
        'email': reset_password_token.user.email,
        'reset_password_url': "https://astrothought.com/reset-password?token={}".format(
            reset_password_token.key)
    }

    # render email text
    reset_password_html = get_template('user-reset-password.html')
    reset_password_plaintext = get_template('user-reset-password.txt')
    send_mail('Reset Password for your Astrothought account!',
              reset_password_plaintext.render(context),
              'AstroThought <noreply@astrothought.com>',
              [reset_password_token.user.email],
              fail_silently=False,
              html_message=reset_password_html.render(context))
