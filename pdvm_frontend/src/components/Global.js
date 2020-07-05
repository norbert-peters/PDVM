//import { createMuiTheme } from '@material-ui/core/styles';
//import { red, blue, } from '@material-ui/core/colors';
import {PdvmCommonTheme} from '../pdvmThemes/pdvmCommonTheme'
import {PdvmDarkTheme} from '../pdvmThemes/pdvmDarkTheme'
import {PdvmLightTheme} from '../pdvmThemes/pdvmLightTheme'


export function selectedTheme(themeType) {
  switch (themeType) {
    case 'common':
      return PdvmCommonTheme
    case 'light':
      return PdvmLightTheme
    case 'dark':
      return PdvmDarkTheme
    default:
      return PdvmCommonTheme
  }
}
