// theme.js
import { blue, grey, lightBlue } from '@material-ui/core/colors';
import { themeColors } from './pdvmColorPalette'

export const theme = {
    back : {
        default : themeColors.back.default,
        inverse: themeColors.back.inverse,
        paper: themeColors.back.paper,
        input: themeColors.back.input,
        inputActiv: themeColors.back.inputActiv,
        inputHover: themeColors.back.inputHover,
        button: themeColors.back.button,
        buttonHover: themeColors.back.buttonHover,
        navbar : themeColors.back.navbar,
    },
    front: {
        default : themeColors.front.default,
        inverse: themeColors.front.inverse,
        text: themeColors.front.text,
        button: themeColors.front.button,
        buttonHover: themeColors.front.buttonHover,
        label: themeColors.front.label,
        labelLight: themeColors.front.labelLight,
        header: themeColors.front.header,
        navbar: themeColors.front.navbar,
    },
    shadow: {
        default: themeColors.shadow.default,
        light: themeColors.shadow.light,
        main: themeColors.shadow.main,
        dark: themeColors.shadow.dark,
    },
    error : {
        light: themeColors.error.light,
        main: themeColors.error.main,
        dark: themeColors.error.dark,
    },    
    typography: {
        fontFamily: themeColors.typography.fontFamily,
        fontSize: themeColors.typography.fontSize,
        fontSizeBig: themeColors.typography.fontSizeBig,
        fontSizeSmall: themeColors.typography.fontSizeSmall,
        fontWeightLight: themeColors.typography.fontWeightLight,
        fontWeightRegular: themeColors.typography.fontWeightRegular,
        fontWeightMedium: themeColors.typography.fontWeightMedium,
        fontWeightBold: themeColors.typography.fontWeightBold,
    },

    palette: {
    primary: {
        light: blue[300],
        main: blue[500],
        dark: blue[700],
    },
    secondary: {
        light: lightBlue[50],
        main: lightBlue[200],
        dark: lightBlue[400],
    },

    type: 'light',
    shadow: {
            light: grey[300],
            main: grey[600],
            dark: grey[900],
    },
    back: {      //Hintergrund
        primary: {      //Allgemein
            light: grey[50],
            main: grey[200],
            dark: grey[400],
        },
        secondary: {        // Sonder
            light: lightBlue[50],
            main: lightBlue[200],
            dark: lightBlue[400],
            },
    },
    text: {         // Texte
        label: {
            light: blue[300],
            main: blue[500],
            dark: blue[700],
        },
        disabled: "rgba(255, 255, 255, 0.5)",
        hint: "rgba(255, 255, 255, 0.5)",
        icon: "rgba(255, 255, 255, 0.5)",
        primary: {      // Allgemein
            light: grey[500],
            main: grey[700],
            dark: grey[900],
        },
        secondary: {       // Sonder
            light: grey[100],
            main: grey[300],
            dark: grey[500],
        },
    },
},

}