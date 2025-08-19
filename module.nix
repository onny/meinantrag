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

		services.uwsgi = {
			enable = true;
			user = "fragify";
			group = "fragify";
			plugins = [ "python3" ];
			instances.fragify = {
				# Align with upstream module: put uwsgi options under settings
				settings = {
					"chdir" = "/";
					"wsgi-file" = "${pkgs.fragify}/share/fragify/fragify_wsgi.py";
					module = "fragify:app";
					# Socket
					"socket" = "unix:${config.services.uwsgi.runDir}/fragify.sock";
					"chmod-socket" = "660";
					umask = "0077";
					vacuum = true;
					master = true;
					processes = 2;
					threads = 2;
					"harakiri" = 60;
					"buffer-size" = 65535;
					"need-app" = true;
					"no-orphans" = true;
					# Serve static files directly via uWSGI (optional)
					# Map /static to packaged assets directory (if present)
					"static-map" = "/static=${pkgs.fragify}/share/fragify/assets";
				};
				# Environment for the WSGI app
				env = {
					FRAGIFY_TEMPLATES_DIR = "${pkgs.fragify}/share/fragify/templates";
					FRAGIFY_STATIC_DIR = "${pkgs.fragify}/share/fragify/assets";
				};
				# Python packages for uWSGI
				pythonPackages = p: with p; [ falcon requests jinja2 ];
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
