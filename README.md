# primary-site-includes

Build creativecommons.org primary site includes (scripts, styles, navigation
header, and navigation footer) based on WordPress REST API


## Code of Conduct

[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md):
> The Creative Commons team is committed to fostering a welcoming community.
> This project and all other Creative Commons open source projects are governed
> by our [Code of Conduct][code_of_conduct]. Please report unacceptable
> behavior to [conduct@creativecommons.org](mailto:conduct@creativecommons.org)
> per our [reporting guidelines][reporting_guide].

[code_of_conduct]:https://creativecommons.github.io/community/code-of-conduct/
[reporting_guide]:https://creativecommons.github.io/community/code-of-conduct/enforcement/


## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).


## WordPress REST API Endpoints

The following endpoints are defined in `creativecommons/wp-theme-creativecommons.org`: [`inc/filters.php`][filtersphp]:
- `/wp-json/ccnavigation-header/menu`
- `/wp-json/ccnavigation-footer/menu`
- `/wp-json/cc-wpscripts/get`
- `/wp-json/cc-wpstyles/get`

[filtersphp]: https://github.com/creativecommons/wp-theme-creativecommons.org/blob/master/inc/filters.php


## Dependencies

- [tartley/**colorama**](https://github.com/tartley/colorama): Simple
  cross-platform colored terminal text in Python
- [pallets/**jinja**](https://github.com/pallets/jinja/): A very fast and
  expressive template engine.
- [psf/**requests**](https://github.com/psf/requests): A simple, yet elegant
  HTTP library.


### Development

- [psf/**black**](https://github.com/psf/black): The uncompromising Python code
  formatter
- [PyCQA / flake8 · GitLab](https://gitlab.com/pycqa/flake8): flake8 is a
  python tool that glues together pep8, pyflakes, mccabe, and third-party
  plugins to check the style and quality of some python code


## License

- [`LICENSE`](LICENSE) (Expat/[MIT][mit] License)

[mit]: http://www.opensource.org/licenses/MIT "The MIT License | Open Source Initiative"
