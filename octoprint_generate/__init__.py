# octoprint_generate/__init__.py
# coding=utf-8
from __future__ import absolute_import
import os
import time

import flask
import requests

import octoprint.plugin
from octoprint.plugin import TemplatePlugin

class OctoPrintGeneratePlugin(octoprint.plugin.SettingsPlugin,
                              TemplatePlugin,
                              octoprint.plugin.AssetPlugin,
                              octoprint.plugin.SimpleApiPlugin,
                              octoprint.plugin.BlueprintPlugin):

    ##— SettingsPlugin —##
    def get_settings_defaults(self):
        return dict(
            text_to_3d_url="https://api.meshy.ai/openapi/v2/text-to-3d",
            image_to_3d_url="https://api.meshy.ai/openapi/v1/image-to-3d",
            api_key=""
        )

    ##— AssetPlugin —##
    def get_assets(self):
        return dict(
            js=["js/generate.js"],
            css=["css/generate.css"]
        )

    ##— TemplatePlugin —##
    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False),
            dict(type="tab", template="generate_tab.jinja2", custom_bindings=True)
        ]

    ##— SimpleApiPlugin —##
    def get_api_commands(self):
        return dict(
            generateText=["prompt"],
            generateImage=["imageData"]
        )

    def on_api_command(self, command, data):
        api_key = self._settings.get(["api_key"])
        headers = {"Authorization": f"Bearer {api_key}"}

        if command == "generateText":
            prompt = data.get("prompt") or flask.abort(400, "Missing prompt")
            url = self._settings.get(["text_to_3d_url"])

            resp = requests.post(
                url,
                json={"mode": "preview", "prompt": prompt},
                headers={**headers, "Content-Type": "application/json"}
            )
            resp.raise_for_status()
            task_id = resp.json().get("result")

            for _ in range(60):
                time.sleep(2)
                status_resp = requests.get(f"{url}/{task_id}", headers=headers)
                status_resp.raise_for_status()
                detail = status_resp.json()
                if detail.get("status") == "SUCCEEDED":
                    model_url = detail["model_urls"]["glb"]
                    break
                if detail.get("status") == "FAILED":
                    flask.abort(500, f"Text-to-3D failed: {detail.get('task_error', {}).get('message','unknown')}")
            else:
                flask.abort(500, "Text-to-3D timed out")

            model_data = requests.get(model_url).content
            filename   = f"text3d_{task_id}.glb"
            self._save_model_file(filename, model_data)
            return dict(filename=filename)

        elif command == "generateImage":
            image_b64 = data.get("imageData") or flask.abort(400, "Missing image data")
            url       = self._settings.get(["image_to_3d_url"])
            data_uri  = f"data:image/png;base64,{image_b64}"

            resp = requests.post(
                url,
                json={"image_url": data_uri, "should_remesh": True, "should_texture": True},
                headers={**headers, "Content-Type": "application/json"}
            )
            resp.raise_for_status()
            task_id = resp.json().get("result")

            for _ in range(60):
                time.sleep(2)
                status_resp = requests.get(f"{url}/{task_id}", headers=headers)
                status_resp.raise_for_status()
                detail = status_resp.json()
                if detail.get("status") == "SUCCEEDED":
                    model_url = detail["model_urls"]["glb"]
                    break
                if detail.get("status") == "FAILED":
                    flask.abort(500, f"Image-to-3D failed: {detail.get('task_error', {}).get('message','unknown')}")
            else:
                flask.abort(500, "Image-to-3D timed out")

            model_data = requests.get(model_url).content
            filename   = f"image3d_{task_id}.glb"
            self._save_model_file(filename, model_data)
            return dict(filename=filename)

    def _save_model_file(self, filename, data):
        base = self._settings.get_basefolder("data")
        models_dir = os.path.join(base, "models")
        os.makedirs(models_dir, exist_ok=True)
        with open(os.path.join(models_dir, filename), "wb") as f:
            f.write(data)

    ##— BlueprintPlugin —##
    @octoprint.plugin.BlueprintPlugin.route("/download", methods=["GET"])
    def download(self):
        filename = flask.request.args.get("file") or flask.abort(400, "Missing file")
        base = self._settings.get_basefolder("data")
        filepath = os.path.join(base, "models", filename)
        if not os.path.isfile(filepath):
            flask.abort(404)
        return flask.send_file(filepath, as_attachment=True)

    def is_blueprint_csrf_protected(self):
        return True


__plugin_name__ = "OctoPrintGenerate"
__plugin_pythoncompat__ = ">=3,<4"
__plugin_implementation__ = OctoPrintGeneratePlugin()
