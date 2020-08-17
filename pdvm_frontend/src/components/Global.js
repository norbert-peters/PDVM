import {theme} from '../theme'


export function selectedTheme(themeType) {
  switch (themeType) {
    case 'common':
      return theme
    case 'light':
      return theme
    case 'dark':
      return theme
    default:
      return theme
  }
}
