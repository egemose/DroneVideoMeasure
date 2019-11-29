var current_frame = 0;
var horizon_fabricjs_ns = null;
var horizon_fabricjs_ew = null;
var horizon_fabricjs_pitch0 = null;
var horizon_fabricjs_pitch45 = null;

// make points only on some frames
fabric.FramePoint = fabric.util.createClass(fabric.Circle, {
  type: 'FramePoint',
  initialize: function(options) {
    this.callSuper('initialize', options);
    this.set('frame', options.frame);
    this.set('name', options.name);
    this.objectCaching = false;
  },
  toObject: function() {
    return fabric.util.object.extend(this.callSuper('toObject'), {
      frame: this.get('frame'),
      name: this.get('name'),
    });
  },
  _render: function(ctx) {
    if (this.get('frame') == current_frame) {
      this.selectable = true;
      this.evented = true;
      this.callSuper('_render', ctx);
    } else {
      this.selectable = false;
      this.evented = false;
    }
  }
});

fabric.FramePoint.fromObject = function(object, callback) {
  object.hasControls = false;
  var frame_point = new fabric.FramePoint(object);
  callback && callback(frame_point);
};

// make lines only on some frames
fabric.FrameLine = fabric.util.createClass(fabric.Line, {
  type: 'FrameLine',
  initialize: function(points, options) {
    this.callSuper('initialize', points, options);
    this.set('frame', options.frame);
    this.set('name', options.name);
    this.objectCaching = false;
  },
  toObject: function() {
    return fabric.util.object.extend(this.callSuper('toObject'), {
      frame: this.get('frame'),
      name: this.get('name'),
    });
  },
  _render: function(ctx) {
    if (this.get('frame') == current_frame) {

      this.selectable = true;
      this.evented = true;
      this.callSuper('_render', ctx);
    } else {
      this.selectable = false;
      this.evented = false;
    }
  }
});

fabric.FrameLine.fromObject = function(object, callback) {
  var points = [object.x1, object.y1, object.x2, object.y2];
  object.hasRotatingPoint = false;
  var frame_line = new fabric.FrameLine(points, object);
  callback && callback(frame_line);
};

// annotate video
class video_annotator {

  constructor(image_url, toolbar_id, video_width, video_height, fps, num_frames) {
    var self = this;
    this.viewer = OpenSeadragon({
      id: "openseadragon",
      toolbar: toolbar_id,
      zoomInButton: "zoom-in",
      zoomOutButton: "zoom-out",
      homeButton: "expand",
      constrainDuringPan: true,
      visibilityRatio: 1,
      minZoomImageRatio: 1,
      maxZoomLevel: 10,
      tileSources: {
        height: video_height,
        width: video_width,
        type: "image",
        url: image_url,
        buildPyramid: false,
      }
    });
    this.overlay = this.viewer.fabricjsOverlay({
      scale: video_width
    });
    this.overlay.fabricCanvas().on('mouse:down', function(event) {
      if (!self.do_draw || self.selection || event.e.target.tagName != "CANVAS") return;
      self.mouse_is_down = true;
      self.viewer.setMouseNavEnabled(!self.mouse_is_down);
      self.start_position = self.overlay.fabricCanvas().getPointer(event.e);
      self.line = new fabric.FrameLine([self.start_position.x, self.start_position.y, self.start_position.x, self.start_position.y], {
        stroke: self.default_stroke,
        strokeWidth: self.default_line_width,
        hasRotatingPoint: false,
        frame: current_frame,
        name: self.current_name,
      });
      self.overlay.fabricCanvas().add(self.line);
    });
    this.overlay.fabricCanvas().on('mouse:move', function(event) {
      if (!self.mouse_is_down || !self.do_draw || self.selection || event.e.target.tagName != "CANVAS") return;
      self.end_position = self.overlay.fabricCanvas().getPointer(event.e);
      self.line.set({
        x2: self.end_position.x,
        y2: self.end_position.y,
      });
      self.overlay.fabricCanvas().renderAll();
    });
    this.overlay.fabricCanvas().on('mouse:up', function(event) {
      if (!self.do_draw || self.selection || event.e.target.tagName != "CANVAS") return;
      self.mouse_is_down = false;
      self.viewer.setMouseNavEnabled(!self.mouse_is_down);
      self.overlay.fabricCanvas().remove(self.line);
      if (self.line.width != 0 && self.line.height != 0) {
        self.overlay.fabricCanvas().add(self.line);
      } else {
        self.point = new fabric.FramePoint({
          radius: self.default_point_size,
          fill: self.default_stroke,
          left: self.start_position.x,
          top: self.start_position.y,
          originX: 'center', originY: 'center',
          hasControls: false,
          frame: current_frame,
          name: self.current_name,
        });
        self.overlay.fabricCanvas().add(self.point);
      };
      self.updateModifications(true);
    });
    this.overlay.fabricCanvas().on("object:selected", function() {
      self.selection = true;
      $('#line_width').prop('disabled', false);
      $('#color_button').prop('disabled', false);
      $('#remove').prop('disabled', false);
    });
    this.overlay.fabricCanvas().on("selection:cleared", function() {
      self.selection = false;
      $('#line_width').prop('disabled', true);
      $('#color_button').prop('disabled', true);
      $('#remove').prop('disabled', true);
    });
    this.overlay.fabricCanvas().on("object:modified", function() {
      self.updateModifications(true);
    });
    this.viewer.addHandler('open', function(event) {
      document.getElementById("openseadragon").querySelector(".openseadragon-canvas").focus();
    });
    this.viewer.gestureSettingsMouse.clickToZoom = false;
    this.navShown = true;
    this.do_draw = false;
    this.show_horizon = false;
    this.selection = false;
    this.mouse_is_down = false;
    this.start_position = {};
    this.end_position = {};
    this.line;
    this.states = [];
    this.mods = 0;
    this.default_stroke = '#FF0000';
    this.default_color_temp = '#FF0000';
    this.default_line_width = 3;
    this.default_point_size = 10;
    this.videoEl = document.getElementById('video');
    this.fabric_video = new fabric.Image(this.videoEl, {
      left: 0,
      top: 0,
      angle: 0,
      originX: 'left',
      originY: 'top',
      objectCaching: false,
      selectable: false,
      evented: false,
      excludeFromExport: true,
    });
    this.num_frames = num_frames
    this.overlay.fabricCanvas().add(this.fabric_video);
    this.video = VideoFrame({
      id: 'video',
      frameRate: fps,
    });
    this.current_name = 'Doodles'
  }

  set_current_name(name) {
    this.current_name = name;
  }

  play_pause() {
    if (this.video.video.paused) {
      this.video.video.play();
      $('#play_pause').html('<i class="fas fa-pause"></i>');
      $('#draw-mode').removeClass('active')
      this.do_draw = false;
    } else {
      this.video.video.pause();
      $('#play_pause').html('<i class="fas fa-play"></i>');
    }
  }

  next_frame() {
    if (this.video.video.paused) {
      this.video.seekForward(1);
    }
  }

  previous_frame() {
    if (this.video.video.paused) {
      this.video.seekBackward(1);
    }
  }

  on_new_frame() {
    var new_frame = this.video.get()
    if (new_frame != current_frame) {
      current_frame = new_frame;
      var progress = current_frame / this.num_frames * 100 + '%';
      $('#video_seek').find('.progress-bar').css('width', progress);
      $('#video_seek').find('.progress-bar').html(this.video.toTime());
      this.draw_horizon();
    } else {
      this.overlay.fabricCanvas().renderAll();
    }
  }

  draw_horizon(callback) {
    var poly_lines = this.overlay.fabricCanvas().getObjects('polyline');
    for (let i in poly_lines) {
      this.overlay.fabricCanvas().remove(poly_lines[i]);
    };
    if (this.show_horizon) {
      $.post($SCRIPT_ROOT + '/get_horizon_fabricjs', {
        frame: current_frame,
      }, function(data) {
        if (data.NS) {
          horizon_fabricjs_ns = new fabric.Polyline(data.NS, {
            stroke: 'red',
            strokeWidth: 3,
            left: data.NS_pos[0].left,
            top: data.NS_pos[0].top,
            selectable: false,
            evented: false,
            excludeFromExport: true,
          });
        } else {
          horizon_fabricjs_ns = null;
        };
        if (data.EW) {
          horizon_fabricjs_ew = new fabric.Polyline(data.EW, {
            stroke: 'blue',
            strokeWidth: 3,
            left: data.EW_pos[0].left,
            top: data.EW_pos[0].top,
            selectable: false,
            evented: false,
            excludeFromExport: true,
          });
        } else {
          horizon_fabricjs_ew = null;
        };
        if (data.pitch0) {
          horizon_fabricjs_pitch0 = new fabric.Polyline(data.pitch0, {
            stroke: 'green',
            strokeWidth: 3,
            left: data.pitch0_pos[0].left,
            top: data.pitch0_pos[0].top,
            selectable: false,
            evented: false,
            excludeFromExport: true,
          });
        } else {
          horizon_fabricjs_pitch0 = null;
        };
        if (data.pitch45) {
          horizon_fabricjs_pitch45 = new fabric.Polyline(data.pitch45, {
            stroke: 'green',
            strokeWidth: 3,
            left: data.pitch45_pos[0].left,
            top: data.pitch45_pos[0].top,
            selectable: false,
            evented: false,
            excludeFromExport: true,
          });
        } else {
          horizon_fabricjs_pitch45 = null;
        };
      }, 'json');
      if (horizon_fabricjs_ns) {
        this.overlay.fabricCanvas().add(horizon_fabricjs_ns);
      };
      if (horizon_fabricjs_ew) {
        this.overlay.fabricCanvas().add(horizon_fabricjs_ew);
      };
      if (horizon_fabricjs_pitch0) {
        this.overlay.fabricCanvas().add(horizon_fabricjs_pitch0);
      };
      if (horizon_fabricjs_pitch45) {
        this.overlay.fabricCanvas().add(horizon_fabricjs_pitch45);
      };
    };
    this.overlay.fabricCanvas().renderAll();
  }

  toggle_draw() {
    this.do_draw = !this.do_draw;
  }

  toggle_horizon() {
    this.show_horizon = !this.show_horizon;
    this.draw_horizon();
  }

  save(save_url) {
    var json = JSON.stringify(this.overlay.fabricCanvas());
    $.post(save_url, {
      fabric_json: json,
      });
  }

  load(json_data) {
    this.overlay.fabricCanvas().loadFromJSON(json_data);
    this.overlay.fabricCanvas().add(this.fabric_video);
    this.overlay.fabricCanvas().sendToBack(this.fabric_video);
    this.updateModifications(true);
  }

  navigate(save_url, to_url) {
    $.when(this.save(save_url)).then(window.location.href = to_url);
  }

  remove() {
    if (!this.overlay.fabricCanvas().getActiveObject()) return;
    this.overlay.fabricCanvas().remove(this.overlay.fabricCanvas().getActiveObject());
    this.updateModifications(true);
  }

  clear() {
    $('#clear_markings_modal').modal('toggle');
  }

  clear_done() {
    this.overlay.fabricCanvas().clear();
    this.overlay.fabricCanvas().add(this.fabric_video);
    this.updateModifications(true);
    $('#clear_markings_modal').modal('toggle');
  }

  updateModifications(savehistory) {
    if (savehistory == true) {
      var myjson = JSON.stringify(this.overlay.fabricCanvas());
      this.states.push(myjson);
      markings_modified(myjson);
    }
  }

  on_undo() {
    if (this.mods < this.states.length) {
      this.overlay.fabricCanvas().clear().renderAll();
      this.overlay.fabricCanvas().loadFromJSON(this.states[this.states.length - 1 - this.mods - 1]);
      this.overlay.fabricCanvas().add(this.fabric_video);
      this.overlay.fabricCanvas().sendToBack(this.fabric_video);
      this.overlay.fabricCanvas().renderAll();
      this.mods += 1;
    }
  }

  on_redo() {
    if (this.mods > 0) {
      this.overlay.fabricCanvas().clear().renderAll();
      this.overlay.fabricCanvas().loadFromJSON(this.states[this.states.length - 1 - this.mods + 1]);
      this.overlay.fabricCanvas().add(this.fabric_video);
      this.overlay.fabricCanvas().sendToBack(this.fabric_video);
      this.overlay.fabricCanvas().renderAll();
      this.mods -= 1;
    }
  }

  on_color_change(event) {
    if (!this.overlay.fabricCanvas().getActiveObject()) return;
    this.overlay.fabricCanvas().getActiveObject().set('stroke', event.value.toHexString());
    this.overlay.fabricCanvas().renderAll();
    this.updateModifications(true);
  }

  on_line_width() {
    if (!this.overlay.fabricCanvas().getActiveObject()) return;
    $('#line_width_modal').modal('toggle');
    var obj = this.overlay.fabricCanvas().getActiveObject();
    if (obj.type == 'FrameLine') {
      $('#line_width_label').text('Line stroke size:');
      $('#model_title').text('Line Stroke Size');
      $('#line_width_input').val(obj.strokeWidth);
    } else if (obj.type == 'FramePoint') {
      $('#line_width_label').text('Point size:');
      $('#model_title').text('Point Size');
      $('#line_width_input').val(obj.radius);
    }
  }

  on_line_width_done() {
    var obj = this.overlay.fabricCanvas().getActiveObject();
    if (!obj) return;
    if (obj.type == 'FrameLine') {
      obj.set('strokeWidth', $('#line_width_input').val());
    } else if (obj.type == 'FramePoint') {
      obj.set('radius', $('#line_width_input').val());
    }
    this.overlay.fabricCanvas().renderAll();
    this.updateModifications(true);
    $('#line_width_modal').modal('toggle');
  }

  on_default() {
    $('#optionsModal').modal('toggle');
    $('#default_line_width').val(this.default_line_width);
    $('#default_color').val(this.default_stroke);
    $('#default_point_size').val(this.default_point_size);
  }

  on_default_color_change(event) {
    this.default_color_temp = event.value.toHexString();
  }

  on_default_done() {
    this.default_stroke = this.default_color_temp;
    this.default_line_width = $('#default_line_width').val();
    this.default_point_size = $('#default_point_size').val();
    $('#optionsModal').modal('toggle');
  }
}
