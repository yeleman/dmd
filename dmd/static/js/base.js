
String.prototype.rsplit = function(sep, maxsplit) {
    var split = this.split(sep);
    return maxsplit ? [ split.slice(0, -maxsplit).join(sep) ].concat(split.slice(-maxsplit)) : split;
}

var graphs = [];
var URL_SEP = "/";
var blank_uuid = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

function swapLastPart(url, lastPart) {
	return swapLastParts(url, [lastPart]);
}

function swapLastParts(url, newParts) {
	var nbParts = newParts.length;
	parts = url.rsplit(URL_SEP);
	// remove unwanted parts
	for (var i=0; i<nbParts ; i++) {
		parts.pop();
	}
	// join new parts
	for (var i=0; i<nbParts ; i++) {
		parts.push(newParts[i]);
	}
	return parts.join(URL_SEP);
}

var get_click_to_point_event = function (url) {
	return {
		click: function (e) { 
			window.location = swapLastPart(url, e.currentTarget.rid);
		}
	}
}
