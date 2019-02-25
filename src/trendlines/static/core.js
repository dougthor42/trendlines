/**
 * Populate the JSTree tree.
 */
function populateTree(data) {
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
  tree.on("changed.jstree", function (e, data) {
  });

  // Go to data pages if they exist, otherwise just open the tree.
  tree.on('select_node.jstree', function(e, data) {
    // jsTree puts the original data structure in a nested object
    // called 'original'. How original of them. Hahaha I crack myself up.
    // If `url` is defined, take us there.
    if (data.node.original.url !== null) {
      var expected = data.node.original.url;
      var new_href = document.location.origin + expected;

      // Take the user to the plot page.
      document.location.href = new_href;
    } else {
      data.instance.toggle_node(data.node);
    };
  });
};


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
