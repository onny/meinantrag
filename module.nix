{
  config,
  lib,
  pkgs,
  ...
}:
let

	cfg = config.services.fragify;

in
{

	options = {
		services.fragify = {

			enable = lib.mkOption {
				type = lib.types.bool;
				default = false;
				description = ''
					Enable fragify web application.
				'';
			};

		};
	};

	config = lib.mkIf cfg.enable {

		# uWSGI application definition for Fragify
		services.uwsgi.enable = true;
		services.uwsgi.user = "fragify";
		services.uwsgi.group = "fragify";
		services.uwsgi.plugins = [ "python3" ];
		services.uwsgi.instance."fragify" = {
			type = "normal";
			chdir = "/";
			# Load WSGI by file path from the packaged share dir
			wsgi-file = "${pkgs.fragify}/share/fragify/fragify_wsgi.py";
			module = "fragify:app";
			pythonPackages = p: with p; [ falcon requests jinja2 ];
			env = {
				FRAGIFY_TEMPLATES_DIR = "${pkgs.fragify}/share/fragify/templates";
				FRAGIFY_STATIC_DIR = "${pkgs.fragify}/share/fragify/assets";
			};
			socket = "unix:${config.services.uwsgi.runDir}/fragify.sock";
			chmod-socket = "660";
			umask = "0077";
			vacuum = true;
			master = true;
			processes = 2;
			threads = 2;
			harakiri = 60;
			buffer-size = 65535;
			# Security hardening
			need-app = true;
			no-orphans = true;
		};

		# Ensure fragify user and group exist
		users.users.fragify = {
			isSystemUser = true;
			group = "fragify";
			description = "fragify web application user";
		};

		users.groups.fragify = {};
	};

	meta = {
		maintainers = with lib.maintainers; [ onny ];
	};
}
