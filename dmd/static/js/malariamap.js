
String.prototype.rsplit = function(sep, maxsplit) {
    var split = this.split(sep);
    return maxsplit ? [ split.slice(0, -maxsplit).join(sep) ].concat(split.slice(-maxsplit)) : split;
}


Array.prototype.getUnique = function(){
   var u = {}, a = [];
   for(var i = 0, l = this.length; i < l; ++i){
      if(u.hasOwnProperty(this[i])) {
         continue;
      }
      a.push(this[i]);
      u[this[i]] = 1;
   }
   return a;
};

function QuantizeIndicatorScale() {

    QuantizeIndicatorScale.prototype.setup = function (manager) {

    	var dataset = manager.currentDataSet();
        var nb_breaks = manager.colors.length;
        if (dataset.length < nb_breaks) {
            nb_breaks = dataset.length;
        }

        this.scale = d3.scale.quantize()
            .domain([d3.min(dataset), d3.max(dataset)])
            .range(d3.range(nb_breaks).map(function(i) { return manager.colors[i]; }));
    };

    QuantizeIndicatorScale.prototype.boundaries_for_color = function (color) {
        return this.scale.invertExtent(color);
    };

    QuantizeIndicatorScale.prototype.color_for_value = function (data) {
        return this.scale(data);
    };

    QuantizeIndicatorScale.prototype.available_colors = function () {
        return this.scale.range();
    };

}

function FixedBoundariesScale(options) {

    this.options = options;

    FixedBoundariesScale.prototype.setup = function (manager) {
        this.colors = [];
        this.min = d3.min(manager.indicator_data_raw);
        this.max = d3.max(manager.indicator_data_raw);

        if (this.options.steps) {
            this.steps = this.options.steps;
            for (var i=0; i < this.steps.length; i++) {
                this.colors.push(manager.colors[i]);
            }
        } else {
            var nb_breaks = manager.colors.length;
            if (manager.indicator_data_raw.length < nb_breaks) {
                nb_breaks = manager.indicator_data_raw.length;
            }

            var step = this.max / nb_breaks;
            var steps = [];
            var current = this.min;
            steps.push(this.min);
            for (var j=0; j< nb_breaks; j++) {
                steps.push(current + step);
                this.colors.push(manager.colors[j]);
            }
            this.steps = steps;
        }
    };

    FixedBoundariesScale.prototype.boundaries_for_color = function (color) {
        var index = this.colors.indexOf(color);
        if (index + 1 >= this.steps.length && this.max > this.steps[index]) {
            upper_bound = this.max;
        } else {
            upper_bound = this.steps[index + 1];
        }

        if (index === 0 && this.min < this.steps[index]) {
            lower_bound = this.min;
        } else {
            lower_bound = this.steps[index];
        }
        return [lower_bound, upper_bound];
    };

    FixedBoundariesScale.prototype.color_for_value = function (data) {
        for (var i=this.steps.length - 1; i>=0; i--) {
            if (data >= this.steps[i]) {
                return this.colors[i];
            }
        }
        return this.colors[this.colors.length -1];
    };

    FixedBoundariesScale.prototype.available_colors = function () {
        return this.colors;
    };
}


function getMalariaMapManager(options) {

    function MalariaMapManager(options) {


    	// Currently selected Indicator
    	this.indicator_slug = null;
    	this.indicator_name = null;

    	// List of all indicators for selected indicator_type
    	this.indicator_list = null;

    	// Currently selected Indicator Type if any
    	this.indicator_type_slug = null;
    	this.indicator_type_name = null;

    	// List of all Indicator Types
    	this.indicator_type_list = options.indicator_type_list || [
    		{value: "survey", label: "Enquête"},
    		{value: "routine", label: "Routine"}];
    	
    	// Currently selected period if any
    	this.period_slug = null;
    	this.period_name = null;

    	// List of all periods
    	this.period_list = options.period_list || null;

    	// Currently selected DPS if any
    	this.dps_slug = null;
    	this.dps_name = null;
    	// List of all DPS
    	this.dps_list = options.dps_list || null;

    	// GeoJSON of all DPS
    	this.dps_geojson = null;

    	// GeoJSON of all ZS within selected DPS
    	this.zs_geojson = {};

    	this.records_data = {};

    	// root UUID (DRC)
    	this.root_slug = options.root_slug || "9616cf8b-5c47-49e2-8702-4f8179565a0c";
    	this.root_name = options.root_name || "R.D.C";

    	// Basic configuration
    	this.initial_latitude = -3.985;
        this.initial_longitude = 25.422;
        this.initial_zoom = 5;
        this.mapID = options.mapID || "map";
        this.mapboxID = options.mapboxID || "mapbox.light";
        this.indicator_api_url = options.indicator_api_url || "/api/malaria/indicators";
        this.geojson_api_url = options.geojson_api_url || "/api/malaria/geojson";
        this.data_api_url = options.data_api_url || "/api/data";

        this.color_initial = '#09192A';
        this.color_is_missing = '#1d3f61'; // '#353f41';
        this.color_not_expected = '#737780'; //'#bfe1e6';
        this.color_regular_point = '#6f9bd1';
        this.color_yes = '#889f37'; //'#28ff00';
        this.color_no = '#4d2c74'; //'#ff1500';
        this.colors = options.colors || ["#fef0d9", "#fdcc8a", "#fc8d59", "#d7301f"];

        this.map = null; // Mapbox map object
        this.scale = null; // Mapbox scale control
        this.legend = null; // Mapbox on-map legend
        this.hc_legend = null; // Mapbox on-map legend for static matrix
        this.infobox = null; // Mapbox infobox control

        // Layers
        this.dps_layer = null;
        this.zs_layer = null;

        this.indicator_scale = options.indicator_scale || new QuantizeIndicatorScale();

        this.title = options.title || null;
        this.subtitle = options.subtitle || null;

        // DOM elements of UI parts.
        this.map_title_e = null; // html title on top of map
        this.map_subtitle_e = null; // html sub title (date/entity)

        this.container_selector = options.container_selector || '.map-options-container';
        this.indicator_type_select = null;
        this.indicator_select = null;
        this.period_select = null;
        this.dps_select = null;

        this.getEmptyOption = function () {
            return $('<option value="-1">AUCUN</option>');
        };

        this.load(options.load, options.onload);

    }

    MalariaMapManager.prototype._prepare_map = function() {
        // remove user interactions
        var options = {
            dragging: false,
            touchZoom: false,
            scrollWheelZoom: false,
            doubleClickZoom: false,
            boxZoom: false,
            zoomControl: false,
            attributionControl: false
        };

        this.map = L.mapbox.map(this.mapID, this.mapboxID, options);

        var manager = this;
        this.map.on('click', function (e) {
        	if (manager.entityIsDPS()) {
        		manager.changeSelectedDPS("-1");
        	}
        });

        // add a scale
        this.scale = L.control.scale({imperial:false})
                              .addTo(this.map);

        this.map.setView([this.initial_latitude, this.initial_longitude],
                         this.initial_zoom);

        this._prepare_map_legend();
        this._prepare_map_infobox();
    };

    MalariaMapManager.prototype._prepare_map_legend = function () {
        var manager = this;

        this.legend = L.control({position: 'bottomright'});
        this.legend.onAdd = function (map) {
            this.div = L.DomUtil.create('div', 'info legend');
            this.update();
            return this.div;
        };
        this.legend.update = function() {

            var labels = [];

            function cleanNum(num) {
                return Math.round(num * 10) / 10;
            }

            $.each(manager.colors, function(index) {
                var color = manager.colors[index];
                var label = null;
                // boundaries = manager.indicator_scale.invertExtent(color);
                boundaries = manager.indicator_scale.boundaries_for_color(color);
                if (boundaries.length == 2 && !isNaN(boundaries[0]) && !isNaN(boundaries[1])) {
                    var from = boundaries[0];
                    var to = boundaries[1];

                    if (index !== 0) { from += 0.1; }

                    labels.push(
                        '<span><i style="background-color:' + color + '"></i> ' +
                        cleanNum(from) + ' – ' +
                        cleanNum(to) + '</span>');
                }
            });

            // SPACER
            if (labels.length) {
                labels.push('<span><i style="background-color:transparent"></i> </span>');
            }

            // NOT EXPECTED
            // labels.push(
            //     '<span><i style="background-color:' + manager.color_not_expected +
            //     '"></i> <abbr title="Aucun rapport attendu pour cet ' +
            //     'indicateur">n/a</abbr></span>');

            // MISSING
            labels.push(
                '<span><i style="background-color:' + manager.color_initial +
                '"></i> <abbr title="Rapport manquant pour calculer cet ' +
                'indicateur">manquant</abbr></span>');

            this.div.innerHTML = labels.join('<br />');
        };
    };

    MalariaMapManager.prototype._prepare_map_infobox = function () {
        var manager = this;
        this.infobox = L.control({position: 'topleft'});
        this.infobox.onAdd = function (map) {
            this._div = L.DomUtil.create('div', 'info');
            this.update();
            return this._div;
        };
        this.infobox.update = function (feature) {
            if (feature === undefined) {
                this._div.innerHTML = 'Déplacez la souris sur les DPS/ZS.';
                return;
            }
            var slug = feature.properties.uuid;
            var dp = manager.currentDataRecord(slug);
            // var text, d = manager.getDataForSlug(feature.properties.slug);

            if (dp === null || dp === undefined)
                text = feature.properties.short_name;
            else
                text = feature.properties.short_name + ' : ' + dp.human;
            this._div.innerHTML = '<strong>' + text + '</strong>';
        };
        this._addInfoBox();
    };

    MalariaMapManager.prototype.IndicatorUrlFor = function(col_type) {
    	var sep = this.indicator_api_url.endsWith("/") ? '' : "/";
        return this.indicator_api_url + sep + col_type;
    };

    MalariaMapManager.prototype._updateIndicatorSelect = function () {
    	var manager = this;
    	this.startLoadingUI();
    	$.get(this.IndicatorUrlFor(this.indicator_type_slug))
        	.done(function (indicator_list) {
        	 	var indic_select = $('#indicator');
        	 	indic_select.empty();
        	 	$.each(indicator_list, function (idx, elem) {
		        	var option = $('<option />');
		        	var label = "#" + elem.number + " " + elem.name;
		        	option.attr('label', label);
		        	option.val(elem.slug);
		        	option.text(label);
		        	indic_select.append(option);
		        });
        	})
        	.always(function () {
        	 	manager.stopLoadingUI();
        	})
    };

    MalariaMapManager.prototype._prepareUI = function() {
        var manager = this;

        createLabelFor = function (selector, text) {
        	var label = $('<label />');
        	label.attr('for', selector);
        	label.text(text);
        	return label;
        }

        updateFromSelect = function (var_key, select) {
        	var value = select.val();
        	var label = select.find(':selected').text();
        	if (value == "-1") {
        		value = null;
        		label = null;
        	}
        	manager[var_key + "_slug"] = value;
        	manager[var_key + "_name"] = label;
        }

        this.options_container = $(this.container_selector);

        // Indicator Type
        this.indicator_type_select = $('<select class="form-control" id="indicator_type" />');
        this.indicator_type_select.append(this.getEmptyOption());
        $.each(this.indicator_type_list, function (idx, elem) {
        	var option = $('<option />');
        	option.attr('label', elem.label);
        	option.val(elem.value);
        	option.text(elem.label);
        	manager.indicator_type_select.append(option);
        });
        this.indicator_type_select.on('change', function (e) {
        	updateFromSelect('indicator_type', $(this));
        	manager._updateIndicatorSelect();
        	$('#indicator').change();
        });

        // Indicator
        this.indicator_select = $('<select class="form-control" id="indicator" />');
        this.indicator_select.append(this.getEmptyOption());
        // other options to be filled on section change
        this.indicator_select.on('change', function (e) {
        	updateFromSelect('indicator', $(this));
        	manager.parametersChanged();
        });

        // Period
        this.period_select = $('<select class="form-control" id="period" />');
        this.period_select.append(this.getEmptyOption());
        var last_year = null;
        var optgroup = null;
        $.each(this.period_list, function (idx, elem) {
        	var year = elem.value.split("-")[0];
        	if (year != last_year) {
        		optgroup = $('<optgroup />');
        		optgroup.attr('label', year);
        		manager.period_select.append(optgroup);
        	}
        	var option = $('<option />');
        	option.attr('label', elem.label);
        	option.val(elem.value);
        	option.text(elem.label);
        	optgroup.append(option);
        	last_year = year;
        });

        this.period_select.on('change', function (e) {
        	updateFromSelect('period', $(this));
        	manager.parametersChanged();
        });

        // DPS
        this.dps_select = $('<select class="form-control" id="dps" />');
        this.dps_select.append(this.getEmptyOption());
        $.each(this.dps_list, function (idx, elem) {
        	var option = $('<option />');
        	option.attr('label', elem.label);
        	option.val(elem.value);
        	option.text(elem.label);
        	manager.dps_select.append(option);
        });
        this.dps_select.on('change', function (e) {
        	updateFromSelect('dps', $(this));
        	manager.parametersChanged();
        });

        // add elements to DOM
        var first_row = $('<form class="form-horizontal col-lg-6" />');
        
        var indicator_type_group = $('<div class="form-group" />');
        indicator_type_group.append(createLabelFor('indicator_type', "Type indic."));
        indicator_type_group.append(this.indicator_type_select);
        first_row.append(indicator_type_group);
        
        var indicator_group = $('<div class="form-group" />');
        indicator_group.append(createLabelFor('indicator', "Indicateur"));
        indicator_group.append(this.indicator_select);
        first_row.append(indicator_group);
        this.options_container.append(first_row);

        var second_row = $('<form class="form-horizontal col-lg-6" />');

        var period_group = $('<div class="form-group" />');
        period_group.append(createLabelFor('period', "Période"));
        period_group.append(this.period_select);
        second_row.append(period_group);

        var dps_group = $('<div class="form-group" />');
        dps_group.append(createLabelFor('dps', "DPS"));
        dps_group.append(this.dps_select);
        second_row.append(dps_group);

        this.options_container.append(second_row);

    };

    MalariaMapManager.prototype.changeSelectedDPS = function(uuid) {
    	this.dps_select.find("option:selected").each(function() {
      			$(this).removeProp('selected');
    	});
    	var option = this.dps_select.find('option[value="' + uuid + '"]');
    	option.prop('selected', 'selected');
    	this.dps_select.change();
    };

    MalariaMapManager.prototype.readyToLoad = function() {
    	return (this.indicator_slug !== null && this.period_slug !== null && this.currentEntity().slug !== null);
    }

	MalariaMapManager.prototype.currentEntity = function() {
		return (this.dps_slug !== null) ? {slug: this.dps_slug, name: this.dps_name} : {slug: this.root_slug, name: this.root_name};
	};

	MalariaMapManager.prototype.dataExistsFor = function(period, entity, indicator) {
		try {
			return indicator in this.records_data[period][entity];
		} catch (e) {
			return false;
		}
    };

    MalariaMapManager.prototype.DataRecordUrlFor = function(period, entity, indicator) {
    	var sep = this.indicator_api_url.endsWith("/") ? '' : "/";
        return this.data_api_url + sep + period + "/" + entity + "/" + indicator;
    };

    MalariaMapManager.prototype.updateDataStoreFor = function(period, entity, indicator, data) {
    	if (!(period in this.records_data))
    		this.records_data[period] = {};

    	if (!(entity in this.records_data[period]))
    		this.records_data[period][entity] = {};

		this.records_data[period][entity][indicator] = data;
    };
    
    MalariaMapManager.prototype.downloadDataFor = function(period, entity, indicator, callback) {
    	var manager = this;
    	pursue = function() {
    		if (callback !== undefined)
    			callback();
    	}

    	if (this.dataExistsFor(period, entity, indicator)) {
    		return pursue();
    	}

    	this.startLoadingUI();
    	$.get(this.DataRecordUrlFor(period, entity, indicator))
    	.done(function (data) {
    		manager.updateDataStoreFor(period, entity, indicator, data);
    	})
    	.always(function (){
    		manager.stopLoadingUI();
    		pursue();
    	});
    };

    MalariaMapManager.prototype.accessDataFor = function(period, entity, indicator, indiv_entity) {
		if (!this.dataExistsFor(period, entity, indicator)) {
			return null;
		}
		var d = this.records_data[period][entity][indicator];
		if (indiv_entity !== undefined)
			return d[indiv_entity];
		return d;
    };

    MalariaMapManager.prototype.retrieveIndicatorData = function(callback) {
    	var entity = this.currentEntity().slug;
    	var period = this.period_slug;
    	var indicator = this.indicator_slug;

    	if (!this.dataExistsFor(period, entity, indicator)) {
			this.downloadDataFor(period, entity, indicator, callback);
		} else {
			if (callback !== undefined)
				callback();
		}
    };

	MalariaMapManager.prototype.currentDataRecord = function(indiv_entity) {
		return this.accessDataFor(this.period_slug,
								  this.currentEntity().slug,
								  this.indicator_slug,
								  indiv_entity);
	};


	MalariaMapManager.prototype.currentDataSet = function() {
		var dataset = [];
		$.each(this.currentDataRecord(), function (index, elem) {
			var value = elem.value;
			if (value !== null) {
				dataset.push(value);
			}
		});
		return dataset;
	};    

    MalariaMapManager.prototype.loadIndicatorData = function() {
    	var manager = this;
    	this.retrieveIndicatorData(function () {
    		var data_record = manager.currentDataRecord();

	    	manager.indicator_scale.setup(manager);

	    	manager.switchLayers();
    		manager.currentLayer().eachLayer(function (layer) {
    			if (layer.feature.properties.uuid in data_record) {
    				var datapoint = data_record[layer.feature.properties.uuid];
    				layer.setStyle({fillColor: manager.getColorFor(datapoint)});
    			}

    			layer.on('mouseover', function(event) {
                    var layer = event.target;
                    manager.infobox.update(layer.feature);
                });

                layer.on('mouseout', function(event) {
                    manager.infobox.update();
                });

                
                layer.on('click', function (event) {
                	if (manager.entityIsDPS()) {
                		return;
                	}
                	var layer = event.target;
                	manager.changeSelectedDPS(layer.feature.properties.uuid);
                });

    		});
    		manager._addLegend();
    	});
    };

    MalariaMapManager.prototype.entityIsDPS = function() {
    	return (this.dps_slug !== null);
    };

    MalariaMapManager.prototype.downloadGeoJSONFor = function(entity, callback) {
    	var manager = this;
    	this.startLoadingUI();
        $.get(this.geoJSONUrlFor(entity), {})
        .done(function (geojson) {
        	if (!(manager.dps_slug in manager.zs_geojson)) {
        		manager.zs_geojson[manager.dps_slug] = {};
        	}
            $.each(geojson, function (key, value) {
            	manager.zs_geojson[manager.dps_slug][key] = value;
            });
        })
        .always(function () {
         	manager.stopLoadingUI();
            if (callback !== undefined) {
                callback();
            }
        });
    };

    MalariaMapManager.prototype.retrieveDPSGeoJSON = function(callback) {
    	var entity = this.currentEntity().slug;

    	if (!(entity in this.zs_geojson)) {
			this.downloadGeoJSONFor(entity, callback);
		} else {
			if (callback !== undefined)
				callback();
		}
    };

    // MalariaMapManager.prototype. = function(callback) {

	MalariaMapManager.prototype.isReady = function () {
        return this.dps_geojson !== null;
    };

    MalariaMapManager.prototype.currentLayer = function() {
    	return this.entityIsDPS() ? this.zs_layer : this.dps_layer;
    };

    MalariaMapManager.prototype.parametersChanged = function() {
        if (!this.isReady() || !this.readyToLoad()) {
            return;
        }

        this._removeLegend();

        var manager = this;

        function continueLoadingIndicator() {
        	manager.loadIndicatorData();
        }

        function continueDisplayDPSLayer() {
        	manager.removeAllLayers();
        	manager.createZSLayer();
        	manager.showZSLayer();
        	continueLoadingIndicator();
        }

        if (this.entityIsDPS()) {
        	this.retrieveDPSGeoJSON(continueDisplayDPSLayer);
        	return;
        } else {
        	continueLoadingIndicator();
        	return;
        }
    };

    MalariaMapManager.prototype._updateTitle = function () {

        var period_str, location_str, indicator_str, title, subtitle;

        if (this.isIndicator()) {
            title = this.current_indicator_name;
            period_str = this.month_name + " " + this.year;
            location_str = this.getCurrentFeature().properties.display_typed_name;
            subtitle = location_str + ", " + period_str;
        } else {
            title = this.getCurrentFeature().properties.display_typed_name;
            subtitle = null;
        }

        this.title = title;
        this.subtitle = subtitle;

        this.map_title_e.text(this.title || "");
        this.map_subtitle_e.text(this.subtitle || "");

    };

    MalariaMapManager.prototype.disableUI = function () {
    	$(this.container_selector).find('select').each(function (idx, elem) {
    		$(elem).attr('disabled', 'disabled');
    	});
    };

    MalariaMapManager.prototype.enableUI = function () {
    	$(this.container_selector).find('select').each(function (idx, elem) {
    		$(elem).removeAttr('disabled');
    	});
    };

    MalariaMapManager.prototype._addInfoBox = function () {
        try {
            this.map.addControl(this.infobox);
        } catch (e) {}
    };

    MalariaMapManager.prototype._removeInfoBox = function () {
        try {
            this.map.removeControl(this.infobox);
        } catch (e) {}
    };

    MalariaMapManager.prototype._addLegend = function () {
        try {
            this.map.addControl(this.legend);
        } catch (e) {}
    };

    MalariaMapManager.prototype._removeLegend = function () {
        try {
            this.map.removeControl(this.legend);
        } catch (e) {}
    };

    MalariaMapManager.prototype.startLoadingUI = function() {
    	this.disableUI();
        this.map.spin(true);
    };

    MalariaMapManager.prototype.stopLoadingUI = function() {
        this.map.spin(false);
        this.enableUI();
    };

    MalariaMapManager.prototype.removeLayer = function(layer) {
    	if (this.map.hasLayer(layer)) {
    		this.map.removeLayer(layer);
    	}

    };

    MalariaMapManager.prototype.removeLayer = function(layer) {
        if (this.map.hasLayer(layer)) {
            this.map.removeLayer(layer);
        }
    };

    MalariaMapManager.prototype.zoomTo = function (layer) {
        if (!layer)
        	return;
        try {
        	var bounds = layer.getBounds();
        } catch (e) {
        	try {
        		var bounds = layer.options.bounds;
        	} catch (ee) {
        		return;
        	}
        }
        try { this.map.fitBounds(bounds); } catch (e) {}
    };

    MalariaMapManager.prototype.updateZoom = function () {
        this.zoomTo(this.currentLayer());
    };


    MalariaMapManager.prototype.prepare = function() {
        this._prepare_map();
        this._prepareUI();
    };

    MalariaMapManager.prototype.geoJSONUrlFor = function(uuid) {
    	var sep = this.geojson_api_url.endsWith("/") ? '' : "/";
        return this.geojson_api_url + sep + uuid;
    };

    MalariaMapManager.prototype.loadDPSGeoJSON = function(callback) {
        var manager = this;
        this.startLoadingUI();
        $.get(this.geoJSONUrlFor(this.root_slug), {})
        .done(function (geojson) {
            // saved geodata as it contains all our polygons & points
            manager.dps_geojson = geojson;

            manager.createDPSLayer();
            manager.showDPSLayer();

            // launch callback
            if (callback !== undefined) {
                callback(this);
            }
        })
        .always(function () {
         	manager.stopLoadingUI();
        });
    };

    MalariaMapManager.prototype.load = function(loadData, callback) {
        this.prepare();
        if (loadData === true) {
            this.loadDPSGeoJSON(callback);
        }
    };

	MalariaMapManager.prototype.removeDPSLayer = function() {
		if (this.dps_layer === null)
			return;
		this.dps_layer.removeLayer(this.map);
	};

	MalariaMapManager.prototype.removeDPSLayers = function() {    
		if (this.dps_layer === null)
			return;

		var manager = this;
		this.dps_layer.clearLayers();
		this.dps_layer = null;
	};

	MalariaMapManager.prototype.removeZSLayer = function() {
		if (this.zs_layer === null)
			return;
		zs_layer.removeLayer(this.map);
	};

	MalariaMapManager.prototype.removeZSLayers = function() {
		if (this.zs_layer === null)
			return;

		var manager = this;
		this.zs_layer.clearLayers();
		this.zs_layer = null;
	};

    MalariaMapManager.prototype.switchLayers = function() {
    	this.removeAllLayers();
    	if (this.entityIsDPS()) {
    		this.createZSLayer();
    		this.showZSLayer();
    	} else {
    		this.createDPSLayer();
    		this.showDPSLayer();
    	}
    };

    MalariaMapManager.prototype.removeAllLayers = function() {
    	this._removeLegend();
    	this.removeZSLayers();
    	this.removeDPSLayers();
    };

    MalariaMapManager.prototype.createDPSLayer = function() {
    	this.removeDPSLayers();
    	var options = {
    		fill: true,
    		fillColor: this.color_initial,
    		fillOpacity: 1,
    		stroke: true,
    		color: "#ffffff",
    		weight: 2,
    	};
    	this.dps_layer = L.geoJson(this.dps_geojson, options);
    };

    MalariaMapManager.prototype.createZSLayer = function(entity) {
    	this.removeZSLayers();

    	var options = {
    		fill: true,
    		fillColor: this.color_initial,
    		fillOpacity: 1,
    		stroke: true,
    		color: "#ffffff",
    		weight: 2,
    	};
    	this.zs_layer = L.geoJson(this.zs_geojson[this.dps_slug], options);
    };

	MalariaMapManager.prototype.showDPSLayer = function() {
		this.removeZSLayer();
    	this.dps_layer.addTo(this.map);
    	this.updateZoom();
    };

    MalariaMapManager.prototype.showZSLayer = function() {
		this.removeDPSLayer();
    	this.zs_layer.addTo(this.map);
    	this.updateZoom();
    };

    MalariaMapManager.prototype.getDataForSlug = function(slug) {
        return this.indicator_data[slug];
    };

    MalariaMapManager.prototype.getHCDataForSlug = function(slug) {
        return this.indicator_data_hc[slug];
    };

    MalariaMapManager.prototype.getColorFor = function(datapoint) {

        if (datapoint === undefined)
            return this.color_is_missing;
        if (datapoint.is_not_expected) {
            return this.color_not_expected;
        }
        if (datapoint.is_missing) {
            return this.color_is_missing;
        }
        var color = this.indicator_scale.color_for_value(datapoint.value);
        if (color === undefined && this.indicator_scale.available_colors().length == 1) {
            color = this.colors[0];
        }
        return color;
    };

    MalariaMapManager.prototype.getColorName = function(color) {
    	index = this.colors.indexOf(color);
    	if (index == -1) {
    		if (color == this.color_is_missing) {
    			return 'MISSING';
    		}
    		if (color == this.color_not_expected) {
    			return 'NOT_EXPECTED';
    		}
    		if (color == this.color_regular_point) {
    			return 'REGULAR';
    		}
    		if (color == this.color_yes) {
    			return 'YES';
    		}
    		if (color == this.color_no) {
    			return 'NO';
    		}
    	} else {
    		return index;
    	}
    };

    MalariaMapManager.prototype.noIndicatorStyle = function (feature) {
        return {
            fillColor: "#6f9bd1",
            weight: 2,
            opacity: 1,
            color: 'white',
            fillOpacity: 1};
    };

    return new MalariaMapManager(options);
}
