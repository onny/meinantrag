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

			enable = lib.mkEnableOption "Fragify web app";

		};
	};

	config = lib.mkIf cfg.enable {

		# uWSGI configuration (nixos-25.05 uses `instance`, not `instances`)
		services.uwsgi.enable = true;
		services.uwsgi.plugins = [ "python3" ];
		services.uwsgi.instance."fragify" = {
			type = "normal";
			chdir = "/";
			# WSGI entry from packaged share dir
			wsgi-file = "${pkgs.fragify}/share/fragify/fragify_wsgi.py";
			module = "fragify:app";
			# Socket
			socket = "unix:${config.services.uwsgi.runDir}/fragify.sock";
			"chmod-socket" = "660";
			umask = "0077";
			vacuum = true;
			master = true;
			processes = 2;
			threads = 2;
			harakiri = 60;
			"buffer-size" = 65535;
			need-app = true;
			"no-orphans" = true;
			# Pass environment to the app
			env = {
				PYTHONPATH = "${pkgs.fragify.pythonPath}";
				FRAGIFY_TEMPLATES_DIR = "${pkgs.fragify}/share/fragify/templates";
				FRAGIFY_STATIC_DIR = "${pkgs.fragify}/share/fragify/assets";
			};
			# Python deps for the embedded interpreter moved to PYTHONPATH in env
			# Extra raw uWSGI settings not covered by module options
			settings = {
				"static-map" = "/static=${pkgs.fragify}/share/fragify/assets";
			};
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
