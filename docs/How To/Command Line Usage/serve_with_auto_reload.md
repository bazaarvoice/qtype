# Serve Applications with Auto-Reload

Enable automatic reloading of your application when YAML files change during development using the `--reload` flag.

### CLI Command

```bash
qtype serve --reload my_app.qtype.yaml
```

### Explanation

- **--reload**: Watches YAML files for changes and automatically restarts the server
- **Development workflow**: Edit your YAML file, save, and immediately see changes without manual restart
- **Port option**: Combine with `-p`/`--port` to specify server port (default: 8000)

### Example with Port

```bash
qtype serve --reload -p 8080 examples/tutorials/01_hello_world.qtype.yaml
```

## See Also

- [Serve Command Reference](../../Reference/CLI.md#serve)
- [Tutorial: Hello World](../../Tutorials/01_hello_world.md)
