
function getEntitiesBrowser (options) {

    function EntitiesBrowser (options) {

        console.log("Creating EntitiesBrowser");

        this.parentID = options.parentID || null;
        this.baseURL = options.baseURL || "/api/entities/getchildren";
        this.lineage = options.lineage || ["pays","centre_sante","division_provinciale_sante","zone_sante","aire_sante"];
        this.auto_launch = options.auto_launch || false;
        this.lineage_data = options.lineage_data || [];
        this.add_default_option = (!options.add_default_option) ? false : true;
        this.default_option_data = options.default_option_data || {value: '-1', label: "Tous"};
        this.root = options.root || null;

        // can't do shit without a parentID
        if (this.parentID === null) {
            return;
        }

        this.parentElem = $('#' + this.parentID);

        console.log("lineage_data");
        console.log(this.lineage_data);

        // register action on change for selects
        this.registerOnChange();

        // if we need to populate first
        if (this.populate_first) {

        }

        // launch
        if (this.auto_launch) {
            var first_level = this.lineage[0];
            var first_select = this.getSelectFor(first_level);
            console.log(first_select);
            var selected_value = this.selectedValueFor(first_level);
            console.log("marking " + first_level + " select with " + selected_value);
            this.setSelectedOn(first_select, selected_value);
            first_select.change();
        }

    }

    EntitiesBrowser.prototype.getEntitySlug = function () {
        for (var i=this.lineage.length - 1; i >= 0 ; i--) {
            var entity = this.getSelectFor(this.lineage[i]).val();
            if (entity && entity != this.default_option_data.value) {
                return entity;
            }
        }
        return this.root;
    };

    EntitiesBrowser.prototype.setSelectedOn = function (selectElem, selected_value) {
        selectElem.children("option[value="+ selected_value +"]").attr('selected', 'selected');
        return selectElem;
    };

    EntitiesBrowser.prototype.getIndexFor = function (type_slug) {
        return this.lineage.indexOf(type_slug);
    };

    EntitiesBrowser.prototype.selectedValueFor = function (type_slug) {
        try {
            return this.lineage_data[this.getIndexFor(type_slug)];
        } catch (e) {
            return null;
        }
    };

    EntitiesBrowser.prototype.getNextLevelFrom = function (type_slug) {
        try {
            return this.lineage[this.getIndexFor(type_slug) + 1];
        } catch (e) {
            return null;
        }
    };

    EntitiesBrowser.prototype.clearSelect = function (selectElem) {
        selectElem.empty();
        if (this.add_default_option) {
            var option = $('<option />');
            option.val(this.default_option_data.value);
            option.text(this.default_option_data.label);
            selectElem.append(option);
        }
        return selectElem;
    };

    EntitiesBrowser.prototype.getSelectFor = function(type_slug) {
        return this.parentElem.find('select.entity_filter[data-level="'+ type_slug +'"]');
    };

    EntitiesBrowser.prototype.registerOnChange = function() {
        var manager = this;
        this.parentElem.find('select.entity_filter').on('change', function (e) {
            e.preventDefault();

            // get selected value. this will be new parent.
            var selected = $(this).val();
            if (selected == manager.default_option_data.value) {
                selected = null;
            }

            var type_slug = $(this).data('level');

            var next_type_slug = manager.getNextLevelFrom(type_slug);
            if (!next_type_slug) {
                return;
            }

            if (selected === null) {
                // we selected an empty one. let's propagate.
                var selectElem = manager.clearSelect(manager.getSelectFor(next_type_slug));
                selectElem.change();
                return;
            }

            // fetch data for next level in lineage and parent = selected
            $.get(manager.baseURL + "/" + selected)
                .success(function (data) {

                    // grab and reset the select for new slug
                    var selectElem = manager.clearSelect(manager.getSelectFor(next_type_slug));

                    // exit if no data
                    if (data[0] === undefined) {
                        return;
                    }

                    // populate with fetched data
                    $.each(data, function (index, entity) {
                        var option = $('<option />');
                        option.val(entity.uuid);
                        option.text(entity.short_name);
                        selectElem.append(option);
                    });

                    // mark selected if exists
                    var selected_value = manager.selectedValueFor(next_type_slug);
                    if (selected_value !== null) {
                        manager.setSelectedOn(selectElem, selected_value);
                        // selectElem.children("option[value="+ selected_value +"]").attr('selected', 'selected');
                        selectElem.change();
                    }
            });
        });
        console.log("registered onChange");
    };

    return new EntitiesBrowser(options);
}

function navigate_for(url, elements) {
	// elements: a list of items to fecth and place in URL (in order !)
	// samples: ['entity', 'period', 'indicator']
	// 			['entity', 'perioda', 'periodb']
	return function (e) {
		e.preventDefault();
		var data = {'entity': "9616cf8b-5c47-49e2-8702-4f8179565a0c"};
		var none = '-1';

		if (elements.includes('entity')) {
			data['zs'] = $('select[data-level="zone_sante"]').val();
			data['dps'] = $('select[data-level="division_provinciale_sante"]').val();
		}
		if (elements.includes('period')) {
			data['period'] = $('select#filter_period').val();
		} 
		if (elements.includes('perioda')) {
			data['perioda'] = $('select#filter_perioda').val();
		}
		if (elements.includes('periodb')) {
			data['periodb'] = $('select#filter_periodb').val();
		}
		if (elements.includes('indicator')) {
			data['indicator'] = $('select#filter_indicator').val();
		}
		
		if (data.zs && data.zs != none) {
			data['entity'] = data['zs'];
		} else if (data.dps && data.dps != none) {
			data['entity'] = data['dps'];
		}

		var parts = [];
		$.each(elements, function (idx, elem) {
			parts.push(data[elem]);
		});
		
		window.location = swapLastParts(url, parts);
	}
}


function register_form_for(url, elements, form_name) {
	if (form_name === undefined) {
		form_name = 'form';
	}
	$(form_name).on('submit', navigate_for(url, elements));
}
