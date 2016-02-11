
function getPNGMalariaMapManager(options) {

    function PNGMalariaMapManager(options) {

    	// Currently selected Indicator
    	this.indicator_slug = null;
    	this.indicator_name = null;
    	this.indicator_number = null;

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
    	this.perioda_slug = null;
    	this.perioda_name = null;
    	this.periodb_slug = null;
    	this.periodb_name = null;

    	// List of all periods
    	this.period_list = options.period_list || null;

    	// Currently selected DPS if any
    	this.dps_slug = null;
    	this.dps_name = null;
    	// List of all DPS
    	this.dps_list = options.dps_list || null;

    	// root UUID (DRC)
    	this.root_slug = options.root_slug || "9616cf8b-5c47-49e2-8702-4f8179565a0c";
    	this.root_name = options.root_name || "RDC";

    	// Basic configuration
    	this.indicator_api_url = options.indicator_api_url || "/api/malaria/indicators";
        this.png_api_url = options.png_api_url || "/api/png";

        this.title = options.title || "Titre";
        this.subtitle = options.subtitle || "Sous titre";

        // DOM elements of UI parts.
        this.map_title_e = null; // html title on top of map
        this.map_subtitle_e = null; // html sub title (date/entity)

        this.map = $('#map'); // img container
        this.image_e = $('#map img');
        this.spinner = new Spinner().spin();

        this.container_selector = options.container_selector || '.map-options-container';
        this.indicator_type_select = null;
        this.indicator_select = null;
        this.period_select = null;
        this.dps_select = null;
        this.export_button = null;

        this.getEmptyOption = function () {
            return $('<option value="-1">AUCUN</option>');
        };

        this.load(options.load, options.onload);

    }

    PNGMalariaMapManager.prototype.load = function(loadData, callback) {
        this.prepare();
        if (loadData === true) {
            // display initial state PNG
        }
    };

    PNGMalariaMapManager.prototype.prepare = function() {
    	this._prepareUI();
    };

    PNGMalariaMapManager.prototype.IndicatorUrlFor = function(col_type) {
    	var sep = this.indicator_api_url.endsWith("/") ? '' : "/";
        return this.indicator_api_url + sep + col_type;
    };

    PNGMalariaMapManager.prototype._updateIndicatorSelect = function () {
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

    PNGMalariaMapManager.prototype._prepareUI = function() {
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
        	manager['indicator_number'] = manager.indicator_name.split(" ", 1)[0].split("#")[1];
        	manager.parametersChanged();
        });

        // Period A
        this.perioda_select = $('<select class="form-control" id="perioda" />');
        this.perioda_select.append(this.getEmptyOption());
        var last_year = null;
        var optgroup = null;
        $.each(this.period_list, function (idx, elem) {
        	var year = elem.value.split("-")[0];
        	if (year != last_year) {
        		optgroup = $('<optgroup />');
        		optgroup.attr('label', year);
        		manager.perioda_select.append(optgroup);
        	}
        	var option = $('<option />');
        	option.attr('label', elem.label);
        	option.val(elem.value);
        	option.text(elem.label);
        	optgroup.append(option);
        	last_year = year;
        });

        this.perioda_select.on('change', function (e) {
        	updateFromSelect('perioda', $(this));
        	manager.parametersChanged();
        });

        // Period B
        this.periodb_select = $('<select class="form-control" id="periodb" />');
        this.periodb_select.append(this.getEmptyOption());
        var last_year = null;
        var optgroup = null;
        $.each(this.period_list, function (idx, elem) {
        	var year = elem.value.split("-")[0];
        	if (year != last_year) {
        		optgroup = $('<optgroup />');
        		optgroup.attr('label', year);
        		manager.periodb_select.append(optgroup);
        	}
        	var option = $('<option />');
        	option.attr('label', elem.label);
        	option.val(elem.value);
        	option.text(elem.label);
        	optgroup.append(option);
        	last_year = year;
        });

        this.periodb_select.on('change', function (e) {
        	updateFromSelect('periodb', $(this));
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
        this.export_button.on('click', function (e) {
        	e.preventDefault();
        	console.log("exporting..");
        });

        // add elements to DOM
        var first_row = $('<form class="form-horizontal first_row col-lg-6" />');
        
        var indicator_type_group = $('<div class="form-group" />');
        indicator_type_group.append(createLabelFor('indicator_type', "Type indic."));
        indicator_type_group.append(this.indicator_type_select);
        first_row.append(indicator_type_group);
        
        var indicator_group = $('<div class="form-group" />');
        indicator_group.append(createLabelFor('indicator', "Indicateur"));
        indicator_group.append(this.indicator_select);
        first_row.append(indicator_group);
        this.options_container.append(first_row);

        var second_row = $('<form class="form-horizontal second_row col-lg-6" />');

        var perioda_group = $('<div class="form-group" />');
        perioda_group.append(createLabelFor('perioda', "Entre"));
        perioda_group.append(this.perioda_select);
        second_row.append(perioda_group);

        var periodb_group = $('<div class="form-group" />');
        periodb_group.append(createLabelFor('periodb', "Et"));
        periodb_group.append(this.periodb_select);
        second_row.append(periodb_group);
        this.options_container.append(second_row);

        var third_row = $('<form class="form-horizontal third_row col-lg-12" />');
        var dps_group = $('<div class="form-group" />');
        dps_group.append(createLabelFor('dps', "DPS"));
        dps_group.append(this.dps_select);
        third_row.append(dps_group);
        this.options_container.append(third_row);

        var fourth_row = $('<form class="form-horizontal fourth_row col-lg-12" />');
        var export_group = $('<div class="form-group exportbuttons" />');
        export_group.append(this.export_button);
        fourth_row.append(export_group);
        this.options_container.append(fourth_row);

        // startup with blank image
        var sep = this.png_api_url.endsWith("/") ? '' : "/";
        this.changePNGSource(this.png_api_url + sep + 'initial.png');
    };

    PNGMalariaMapManager.prototype.changePNGSource = function(url) {
    	var manager = this;
    	this.startLoadingUI();
    	this.image_e.load(function (){
    		manager.stopLoadingUI();
    	});
		this.image_e.attr('src', url);
    	
    };

    PNGMalariaMapManager.prototype.currentEntity = function() {
		return (this.dps_slug !== null) ? {slug: this.dps_slug, name: this.dps_name} : {slug: this.root_slug, name: this.root_name};
	};

	PNGMalariaMapManager.prototype.hasPeriod = function() {
		if (this.perioda_slug !== null || this.periodb_slug !== null) {
			return this.periods_slug();
		} else {
			return null;
		}
	};

	PNGMalariaMapManager.prototype.periods_slug = function() {
		if (this.perioda_slug !== null && this.periodb_slug !== null) {
			return this.perioda_slug + '_' + this.periodb_slug;
		} else {
			var pstr = (this.perioda_slug !== null) ? this.perioda_slug : this.periodb_slug;
			return pstr + '_' + pstr;
		}
	};

    PNGMalariaMapManager.prototype.readyToLoad = function() {
    	return (this.indicator_number !== null && this.hasPeriod() !== null && this.currentEntity().slug !== null);
    }

    PNGMalariaMapManager.prototype.PNGMapUrlFor = function(period, entity_name, indicator_number) {
    	var sep = this.png_api_url.endsWith("/") ? '' : "/";
        return this.png_api_url + sep + period + "_" + entity_name + "_indic" + indicator_number + ".png";
    };

    PNGMalariaMapManager.prototype.parametersChanged = function() {
        if (!this.readyToLoad()) {
            return;
        }

        var entity = this.currentEntity().slug;
        var entity_name = this.currentEntity().name;
    	var period = this.periods_slug();
    	var indicator_number = this.indicator_number;

    	var url = this.PNGMapUrlFor(period, entity_name, indicator_number);

  		this.changePNGSource(url);
    };

    PNGMalariaMapManager.prototype._updateTitle = function () {

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

    PNGMalariaMapManager.prototype.startLoadingUI = function() {
    	this.disableUI();
        this.map.spin(true);
    };

    PNGMalariaMapManager.prototype.stopLoadingUI = function() {
        this.map.spin(false);
        this.enableUI();
    };

    PNGMalariaMapManager.prototype.disableUI = function () {
    	$(this.container_selector).find('select, button').each(function (idx, elem) {
    		$(elem).attr('disabled', 'disabled');
    	});
    };

    PNGMalariaMapManager.prototype.enableUI = function () {
    	$(this.container_selector).find('select, button').each(function (idx, elem) {
    		$(elem).removeAttr('disabled');
    	});
    };


    return new PNGMalariaMapManager(options);
}
