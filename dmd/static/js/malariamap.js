
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

var OPACITY = 1;

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

function QuantileIndicatorScale() {

    QuantileIndicatorScale.prototype.setup = function (manager) {

    	var dataset = manager.currentDataSet();
        var nb_breaks = manager.colors.length;
        if (dataset.length < nb_breaks) {
            nb_breaks = dataset.length;
        }

        this.scale = d3.scale.quantile()
            .domain([d3.min(dataset), d3.max(dataset)])
            .range(d3.range(nb_breaks).map(function(i) { return manager.colors[i]; }));
    };

    QuantileIndicatorScale.prototype.boundaries_for_color = function (color) {
        return this.scale.invertExtent(color);
    };

    QuantileIndicatorScale.prototype.color_for_value = function (data) {
        return this.scale(data);
    };

    QuantileIndicatorScale.prototype.available_colors = function () {
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
        this.mapboxID = options.mapboxID || null; //"mapbox.light";
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

        this.indicator_scale = options.indicator_scale || new QuantileIndicatorScale();

        this.title = options.title || "Super titre";
        this.subtitle = options.subtitle || "un sous titre";

        // DOM elements of UI parts.
        this.map_title_e = null; // html title on top of map
        this.map_subtitle_e = null; // html sub title (date/entity)

        this.container_selector = options.container_selector || '.map-options-container';
        this.indicator_type_select = null;
        this.indicator_select = null;
        this.period_select = null;
        this.dps_select = null;
        this.export_button = null;

        // Export map marker
        this.static_map = options.static_map || false;
        this.exporter = null;

        this.getEmptyOption = function () {
            return $('<option value="-1">AUCUN</option>');
        };

        this.load(options.load, options.onload);

    }

    // Export related members
    MalariaMapManager.prototype.export_props = function() {
        return {
            indicator_slug: this.indicator_slug,
			indicator_name: this.indicator_name,
			indicator_type_slug: this.indicator_type_slug,
			indicator_type_name: this.indicator_type_name,
			period_slug: this.period_slug,
			period_name: this.period_name,
			dps_slug: this.dps_slug,
			dps_name: this.dps_name,
			dps_geojson: this.dps_geojson,
			zs_geojson: this.zs_geojson,
			records_data: this.records_data,
			root_slug: this.root_slug,
			root_name: this.root_name,
			mapID: this.mapID,
			map: this.map,
			mapboxID: this.mapboxID,
			title: this.title,
			subtitle: this.subtitle,
        };
    };

    MalariaMapManager.prototype.loadStaticMap = function(callback) {

        // // add legend
        // this._addLegend();
        // if (this.isDistrict()) {
        //     this._prepare_map_hc_legend();
        //     this.map.addControl(this.hc_legend);
        // }

        // var indicator_data_hc = this.indicator_data_hc;

        // // display the layers we have
        // if (this.indicator_data) {
        //     this.displayDistrictLayer(this.indicator_data);
        // }

        // // display HC layer
        // if (this.isDistrict() && Object.keys(indicator_data_hc).length) {
        //     this.displayHCLayer(indicator_data_hc);
        // }

        // // zoom to current feature
        // this.updateZoom();

        if (callback !== undefined) {
            callback(this);
        }
    };

    MalariaMapManager.prototype._prepare_map = function() {
        // remove user interactions
        var options = {
            dragging: false,
            touchZoom: false,
            scrollWheelZoom: false,
            doubleClickZoom: false,
            boxZoom: false,
            zoomControl: true,
            attributionControl: false,
            minZoom: 4,
            maxZoom: 10,
        };

        // remove UI features on export
        if (this.static_map) {
            options.fadeAnimation = false;
            options.zoomAnimation = false;
            options.markerZoomAnimation = false;
        }

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

        // not for export
        if (!this.static_map) {
        	this._prepare_map_legend();
            this._prepare_map_infobox();
        }
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
                        '<span><i style="background-color:' + color + '; opacity:' + OPACITY + ';"></i> ' +
                        cleanNum(from) + ' – ' +
                        cleanNum(to) + '</span>');
                }
            });

            // SPACER
            if (labels.length) {
                labels.push('<span><i style="background-color:transparent"></i> </span>');
            }

            // MISSING
            labels.push(
                '<span><i style="background-color:' + manager.color_initial +
                '; opacity:' + OPACITY + ';"></i> <abbr title="Rapport manquant pour calculer cet ' +
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

        // Export Button
        this.export_button = $('<button id="export_map_btn" 	disabled="disabled" class="btn btn-default btn-primary">Exporter</button>');
        // this.export_button.on('click', function (e) {
        // 	e.preventDefault();
        // 	console.log("exporting..");
        // });

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

        var third_row = $('<form class="form-horizontal col-lg-12" />');
        var export_group = $('<div class="form-group exportbuttons" />');
        export_group.append(this.export_button);
        third_row.append(export_group);
        this.options_container.append(third_row);

        // setup exporter
        this.exporter = getMapExporter({mapManager: this, auto_click:true});

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
    				layer.setStyle({fillColor: manager.getColorFor(datapoint),
    							    fillOpacity: OPACITY});
    			}

    			// interactivity (not for export)
    			if (!manager.static_map) {
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
	            }

    		});
    		manager._addLegend();
    	});
    };

    MalariaMapManager.prototype.entityIsDPS = function() {
    	return (this.dps_slug !== null);
    };

    MalariaMapManager.prototype.downloadAllDPSGeoJSON = function(callback) {
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

    MalariaMapManager.prototype.retrieveAllDPSGeoJSON = function(callback) {
    	if (!this.dps_geojson) {
			this.downloadAllDPSGeoJSON(callback);
		} else {
			if (callback !== undefined)
				callback();
		}
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
    	$(this.container_selector).find('select, button').each(function (idx, elem) {
    		$(elem).attr('disabled', 'disabled');
    	});
    };

    MalariaMapManager.prototype.enableUI = function () {
    	$(this.container_selector).find('select, button').each(function (idx, elem) {
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
        if (!this.static_map) {
        	this._prepareUI();
        }
    };

    MalariaMapManager.prototype.geoJSONUrlFor = function(uuid) {
    	var sep = this.geojson_api_url.endsWith("/") ? '' : "/";
        return this.geojson_api_url + sep + uuid;
    };

    MalariaMapManager.prototype.loadDPSGeoJSON = function(callback) {
        this.retrieveAllDPSGeoJSON(callback);
    };

    MalariaMapManager.prototype.load = function(loadData, callback) {
        this.prepare();
        if (loadData === true) {
            this.loadDPSGeoJSON(callback);
        }
        if (this.static_map === true) {
            this.loadStaticMap(callback);
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
    		fillOpacity: OPACITY,
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
    		fillOpacity: OPACITY,
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
            opacity: OPACITY,
            color: 'white',
            fillOpacity: 1};
    };

    return new MalariaMapManager(options);
}

function roundRect(ctx, x, y, width, height, radius, fill, stroke) {
  if (typeof stroke == "undefined" ) {
    stroke = true;
  }
  if (typeof radius === "undefined") {
    radius = 5;
  }
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(x + width - radius, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
  ctx.lineTo(x + width, y + height - radius);
  ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  ctx.lineTo(x + radius, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
  ctx.lineTo(x, y + radius);
  ctx.quadraticCurveTo(x, y, x + radius, y);
  ctx.closePath();
  if (stroke) {
    ctx.stroke();
  }
  if (fill) {
    ctx.fill();
  }
}


function getMapExporter(options) {

    function MapExporter (options) {
        this.buttonID = options.buttonID || "export_map_btn";
        this.button = $('#' + this.buttonID);
        this.mapID = options.mapID || "exported_map";
        this.mapManager = options.mapManager;
        this.auto_click = options.auto_click || false;
        this.exportedMapManager = null;
        this.timer = null;

        this.registerButton();
    }

    MapExporter.prototype.removeTimeout = function () {
        clearTimeout(this.timer);
    };

    MapExporter.prototype.registerButton = function() {
        var manager = this;
        this.button.on('click', function (e) {
            e.preventDefault();

            if ($('html').is('.ie6, .ie7, .ie8, .ie9')) {
                alert("ATTENTION!\nL'export de la cartographie n'est pas " +
                      "possible avec Internet Explorer 9 et plus ancien.\n" +
                      "Merci d'utiliser une version plus récente d'Internet " +
                      "Explorer ou un autre navigateur tel Mozilla Firefox " +
                      "ou Google Chrome.");
                return;
            }

            // make sure we launch it only once until it finishes.
            var state = $(this).attr('disabled');
            // var timer;
            var cancel = function() {
                console.log("cancelled.");
                manager.removeTimeout();
                manager.resetButton();
                manager.restoreButton();
            };
            if (state != 'disabled') {
                try {
                    manager.timer = setTimeout(cancel, 90000);
                    manager.do_export();
                } catch(exp) {
                    console.log("Error while exporting.");
                    console.log(exp.toString());
                    cancel();
                }
            }
        });
        this.restoreButton();
    };

    MapExporter.prototype.makeButtonPending = function () {
        this.button.html('<i class="fa fa-spinner faa-spin animated"></i> en cours…');
        this.button.attr('disabled', 'disabled');
    };

    MapExporter.prototype.restoreButton = function () {
        this.button.text('Exporter');
        this.button.removeAttr('disabled');
    };

    MapExporter.prototype.resetButton = function () {
        $('.exportbuttons .save-as-png').remove();
        $('#' + this.mapID).remove();
        $('#page-inner').append('<div id="exported_map" />');
    };

    MapExporter.prototype.do_export = function() {
        console.log("Exporting map…");

        // reset button state
        this.resetButton();
        this.makeButtonPending();

        // prepare static map options
        var options = this.mapManager.export_props();
        options.static_map = true;
        options.mapID = this.mapID;

        var manager = this;
        console.log("ready to doImage");
        options.onload = function (mmap) {
        	console.log("onload");

            function cssvalue(elem, prop) {
                return parseInt(elem.css(prop).replace('px', ''));
            }

            var map = mmap.map;
            doImage = function (err, canvas) {

            	console.log("inside doImage");
                var titleSizePx = 22;
                var titleHeight = titleSizePx + Math.round(titleSizePx * 0.25);
                var subtitleSizePx = 16;
                var subtitleHeight = subtitleSizePx + Math.round(subtitleSizePx * 0.25);
                var subtitleHeightPosition = (titleHeight + (subtitleHeight - (titleSizePx / 2)));
                var textHeight = titleHeight;
                if (manager.mapManager.subtitle) {
                    textHeight += subtitleHeight;
                }

                var new_can = $('#canvas')[0];
                new_can.width = canvas.width;
                new_can.height = canvas.height + textHeight;
                var canvasWidth = new_can.width;
                var canvasHeight = new_can.height;
                var ctx = new_can.getContext("2d");
                // fill with white
                ctx.fillStyle = "rgb(255,255,255)";
                ctx.fillRect(0, 0, new_can.width, new_can.height);
                console.log(ctx);
                console.log(canvas);
                console.log(textHeight);
                try {
                	ctx.drawImage(canvas, 0, textHeight);
                } catch (e) { console.error(e.toString()); }

                // draw title
                ctx.fillStyle = "black";
                ctx.font = titleSizePx + "px 'Droid Sans',sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";

                // draw subtitle
                ctx.fillText(manager.mapManager.title, new_can.width / 2 , (titleHeight - (titleSizePx / 2)));
                if (manager.mapManager.subtitle !== null) {
                    ctx.font = subtitleSizePx + "px 'Droid Sans',sans-serif";
                    ctx.fillText(manager.mapManager.subtitle, new_can.width / 2 , subtitleHeightPosition);
                }

                // draw scale
                var leafletScaleWidth = parseInt($('#'+ manager.mapID +' .leaflet-control-scale-line').css('width').replace('px', ''));
                var scaleHeight = 16;
                var scaleWidth = leafletScaleWidth; // 74
                var scaleLeft = 10;
                var scaleBottom = new_can.height - 10;
                var scaleColor = "#333333";
                // draw white .5 opacity rect
                ctx.fillStyle = "rgba(255,255,255, 0.5)";
                ctx.fillRect(scaleLeft, scaleBottom - scaleHeight,
                             scaleWidth, scaleHeight);
                // draw border
                ctx.strokeStyle = scaleColor;
                ctx.lineWidth = 2;
                ctx.lineJoin = 'round';
                ctx.lineCap = 'round';
                ctx.beginPath();
                ctx.moveTo(scaleLeft, scaleBottom - scaleHeight);
                ctx.lineTo(scaleLeft, scaleBottom);
                ctx.lineTo(scaleLeft + scaleWidth, scaleBottom);
                ctx.lineTo(scaleLeft + scaleWidth, scaleBottom - scaleHeight);
                ctx.stroke();
                // draw text
                var scale_text = $('#'+ manager.mapID +' .leaflet-control-scale-line').text();
                ctx.fillStyle = scaleColor;
                ctx.font = "11px 'Droid Sans',sans-serif";
                ctx.textAlign = "left";
                ctx.textBaseline = "bottom";
                ctx.fillText(scale_text, scaleLeft + 2, scaleBottom - 1);

                // // draw legend
                // var html_legend = $('#' + manager.mapID + ' .legend');
                // if (html_legend.length) {
                //     var legendWidth = cssvalue(html_legend, 'width');
                //     var legendHeight = cssvalue(html_legend, 'height');
                //     var legendMarginRight = cssvalue(html_legend, 'margin-right');
                //     var legendMarginBottom = cssvalue(html_legend, 'margin-bottom');
                //     var legendPaddingLeft = cssvalue(html_legend, 'padding-left');
                //     var legendPaddingTop = cssvalue(html_legend, 'padding-top');
                //     var legendX = canvasWidth - legendWidth - legendMarginRight;
                //     var legendY = canvasHeight - legendHeight - legendMarginBottom;
                //     ctx.fillStyle = "rgba(255,255,255, 0.8)";
                //     ctx.strokeStyle = '#bbbbbb';
                //     roundRect(ctx, legendX, legendY,
                //               legendWidth, legendHeight, 5, true, true);
                //     // draw legend text
                //     ctx.shadowOffsetX = 0;
                //     ctx.shadowOffsetY = 0;
                //     ctx.shadowBlur = 0;
                //     var legendTextX = legendX + legendPaddingLeft;
                //     var legendTextY = legendY + legendPaddingTop;
                //     var currentLegendTextY = legendTextY;
                //     html_legend.children('span').each(function (index, spanElem) {
                //         var span = $(spanElem);
                //         var i = span.children('i');
                //         var width = cssvalue(i, 'width');
                //         var height = cssvalue(i, 'height');
                //         var text = span.text();
                //         ctx.fillStyle = i.css('background-color');
                //         ctx.fillRect(legendTextX, currentLegendTextY,
                //                       width, height);
                //         // text
                //         ctx.fillStyle = scaleColor;
                //         ctx.font = "12px 'Droid Sans',sans-serif";
                //         ctx.textAlign = "left";
                //         ctx.textBaseline = "middle";
                //         ctx.fillText(text,
                //                      legendTextX + width,
                //                      currentLegendTextY + height / 2);
                //         currentLegendTextY += height;
                //     });
                // }

                // // draw HC legend
                // var html_hc_legend = $('#' + manager.mapID + ' .hc_legend');
                // if (html_hc_legend.length) {
                //     var hcLegendWidth = cssvalue(html_hc_legend, 'width');
                //     var hcLegendHeight = cssvalue(html_hc_legend, 'height');
                //     var hcLegendMarginLeft = cssvalue(html_hc_legend, 'margin-left');
                //     var hcLegendMarginTop = cssvalue(html_hc_legend, 'margin-top');
                //     var hcLegendPaddingLeft = cssvalue(html_hc_legend, 'padding-left');
                //     var hcLegendPaddingTop = cssvalue(html_hc_legend, 'padding-top');
                //     var hcLegendX = hcLegendMarginLeft;
                //     var hcLegendY = hcLegendMarginTop + textHeight;
                //     ctx.strokeStyle = '#bbbbbb';
                //     ctx.fillStyle = "rgba(255,255,255, 0.8)";
                //     ctx.shadowOffsetX = 0;
                //     ctx.shadowOffsetY = 0;
                //     ctx.shadowBlur = 0;
                //     ctx.shadowColor = scaleColor;
                //     roundRect(ctx, hcLegendX, hcLegendY,
                //               hcLegendWidth, hcLegendHeight, 5, true, true);
                //     var currentHcLegendTextY = hcLegendY + hcLegendPaddingTop;
                //     var oddColor = "rgba(33,33,33, 0.1)";
                //     var evenColor = "rgba(255,255,255, 0.8)";
                //     $('.hc_line').each(function (index, spanElem) {
                //         var span = $(spanElem);
                //         var width = cssvalue(span, 'width');
                //         var height = 10; //cssvalue(span, 'height');
                //         height -= 1;
                //         var text = span.text();
                //         // text
                //         ctx.fillStyle = (index % 2 === 0) ? null : oddColor;
                //         if (index % 2 !== 0) {
                //             ctx.fillRect(hcLegendX, currentHcLegendTextY,
                //                           hcLegendWidth, height);
                //         }
                //         ctx.fillStyle = scaleColor;
                //         ctx.font = "9px droid_sans_monoregular";
                //         ctx.textAlign = "left";
                //         ctx.textBaseline = "middle";
                //         ctx.fillText(text,
                //                      hcLegendX + hcLegendPaddingLeft,
                //                      currentHcLegendTextY + height / 2);
                //         currentHcLegendTextY += height;
                //     });
                // }

                console.log("done doImage");

                var url = new_can.toDataURL();
                var link = $('<a />');
                link.attr('href', url);
                link.attr('download', 'exported_map.png');
                link.attr('class', 'save-as-png btn btn-default');
                link.html('<i class="fa fa-floppy-o"></i>');
                link.attr('title', "Enregistrer l'image PNG");
                $('.exportbuttons').append(link);

                // remove map
                $('#' + manager.mapID).remove();

                // toggle back
                manager.restoreButton();

                // emulate a click on the created button to popup save dialog
                if (manager.auto_click === true) {
                    var e = document.createEvent("MouseEvents");
                    e.initMouseEvent("click", true, true, window, 0, 0, 0, 0, 0,
                                     false, false, false, false, 0, null);
                    link[0].dispatchEvent(e);
                }

                manager.removeTimeout();
            };

            // wait 2s between map creation and exporting to canvas
            // to allow any animation to complete
            var interval;
            console.log("starting interval");
            interval = setInterval(function (){
                clearInterval(interval);
                console.log("launching leafletImage");
                leafletImage(map, doImage);
            }, 2000);

        };
        this.exportedMapManager = getMalariaMapManager(options);

    };
    console.log("Registering getMapExporter");
    return new MapExporter(options);
}
