$(function() {
  function GenerateViewModel(parameters) {
    var self = this;
    self.settings = parameters[0];

    self.textPrompt        = ko.observable("");
    self.imageData         = ko.observable(null);
    self.generatedFileUrl  = ko.observable("");
    self.generatedFileName = ko.observable("");

    self.generateTextModel = function() {
      self.generatedFileUrl("");
      self.generatedFileName("");
      OctoPrint.simpleApiCommand("generate", "generateText", { prompt: self.textPrompt() })
        .done(function(response) {
          self.generatedFileName(response.filename);
          self.generatedFileUrl("/plugin/generate/download?file=" + encodeURIComponent(response.filename));
        });
    };

    self.onImageSelected = function(_, event) {
      var file = event.target.files[0];
      if (!file) return;
      var reader = new FileReader();
      reader.onload = function(e) {
        var b64 = e.target.result.split(",")[1];
        self.imageData(b64);
      };
      reader.readAsDataURL(file);
    };

    self.generateImageModel = function() {
      self.generatedFileUrl("");
      self.generatedFileName("");
      OctoPrint.simpleApiCommand("generate", "generateImage", { imageData: self.imageData() })
        .done(function(response) {
          self.generatedFileName(response.filename);
          self.generatedFileUrl("/plugin/generate/download?file=" + encodeURIComponent(response.filename));
        });
    };
  }

  OCTOPRINT_VIEWMODELS.push([
    GenerateViewModel,
    ["settingsViewModel"],
    ["#tab_plugin_generate"]
  ]);
});
