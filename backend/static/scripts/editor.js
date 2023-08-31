initEditorInstance = function (editor) {
  var editorParent = document.querySelector(tinyMCE.settings.selector);
  if (!editorParent.value) {
    editor.setContent(editorParent.getAttribute('rich_placeholder'));
    editor.on('focus', function () {
      editor.setContent('');
      editor.off('focus');
    });
  }
}
