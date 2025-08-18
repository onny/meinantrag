{ pkgs, ... }:
{

  environment.etc."mail-quota-warning-secrets.yml".text = ''
    accounts:
      - name: Sales
        imap_server: mail.example.com
        imap_port: 993
        username: sales@example.com
        password: secret

      - name: Support
        imap_server: mail.example.com
        imap_port: 993
        username: support@example.com
        password: secret

    mail:
      smtp_server: mail.example.com
      smtp_port: 587
      smtp_username: monitoring@example.com
      smtp_password: secret
      from_address: monitoring@example.com
      recipients:
        - admin1@example.com
        - admin2@example.com
  '';

  services.mail-quota-warning = {
    enable = true;
    settings = {
      CHECK_INTERVAL_DAYS = 7;
      QUOTA_WARNING_THRESHOLD_PERCENT = 80;
    };
    secretFile = /etc/mail-quota-warning-secrets.yml;
  };

}
