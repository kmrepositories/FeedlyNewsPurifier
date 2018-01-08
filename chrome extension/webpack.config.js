module.exports = {
    entry: "./browserifyInput.js",
    output: {
        filename: 'backgroundscript.js'
    },
	 module: {
    rules: [
      { test: /\.(glsl|frag|vert)$/, use: ['raw-loader', 'glslify-loader']}
    ]
  },
	node: {
    fs: 'empty'
  }
}