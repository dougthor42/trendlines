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
