/**
 * Populate the JSTree tree.
 */
function populateTree(data, metricId) {
  var tree = $('#jstree-div');

  // Create an instance when the DOM is ready.
  tree.jstree(
    {
      'core': {
        'data' : data
      }
    }
  );

  // Bind events.

  // This event allows us to select a node via `metricId` argument. When the
  // tree is done populating, the `selectNodeById` function is fired. We need to
  // wait for the the tree to be fully ready or else the `select_node` method
  // will fail.
  tree.on("ready.jstree", function(e, data){
    console.log("tree ready");
    selectNodeById(tree, metricId);
  });

  tree.on("changed.jstree", function (e, data) {
  });

  tree.on("loaded.jstree", function () {
    tree.jstree('open_all');
  });

  tree.on('select_node.jstree', function(e, data) {
    treeChanged(e, data);
  });
};


/*
 * Update the plot if data exists, otherwise just open the tree.
 * This is called when the `select_node` event is seen.
 */
function treeChanged(e, data) {
  // If `metric_id` is defined, then we can query data
  if (data.node.original.metric_id !== null) {
    var expected = "/api/v1/data/" + data.node.original.metric_id;
    // grab the plot data from the api
    $.getJSON(expected)
      .done(function(jsonData) {
        makePlot(jsonData);

        // This updates the URL to reflect which plot is shown.
        var history_url = "/plot/" + data.node.original.metric_id;
        window.history.pushState('page2', 'Title', history_url);
      })
      .fail(function(jqXHR, textStatus, errorThrown) {
        console.log("Request failed: " + errorThrown);
      });
  } else {
    // Otherwise just open/close the tree node.
    data.instance.toggle_node(data.node);
  };
}


/*
 * Select a specific tree element.
 * Called when both:
 *   (a) a metric_id is given in the URL and
 *   (b) the jsTree object has fully loaded.
 */
function selectNodeById(tree, metricId) {
  if (typeof metricId === 'undefined') {
    // We were given a metric ID, so let's select it in the jstree
    tree.jstree('select_node', metricId);
  }

}


/**
 * Make the plotly Plot
 */
function makePlot(data) {
  TESTER = document.getElementById('graph');

  // I think Plotly only accepts 1D arrays of data, so split things out.
  var x = data.rows.map(function (obj) {return obj.timestamp});
  var y = data.rows.map(function (obj) {return obj.value});
  var n = data.rows.map(function (obj) {return obj.n});
  var units = data.units;

  trace1 = {
    x: n,
    y: y,
    type: 'scatter'
  };

  layout = {
    yaxis: {
      title: units
    }
  };

  trace = [ trace1 ];
  Plotly.plot(TESTER, trace, layout);

  $(document).ready(
    function() {
      $(":radio[name='x-axis-type']").change(
        function() {
          // Determine which x scale to use.
          if (this.value == "time") {
            new_x = x;
          } else if (this.value == "sequential") {
            new_x = n;
          }

          // Adjust the x values of the data.
          Plotly.restyle(TESTER, 'x', [new_x]);
        }
      )
    }
  );
}
