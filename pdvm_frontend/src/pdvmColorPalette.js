// pdvmColorPalette.js
/*
Hier werden die Farbchematas bereitgestellt. Zur Entwicklung sind diese hier mal fix.
In einem späterenen Entwicklungsstadium werden die Daten in der Datenbank abgelegt 
und damit individuell änderbar.
*/
import { red, blue, grey, lightBlue, teal, blueGrey } from '@material-ui/core/colors';
import {
    darken,
    lighten,
  } from '@material-ui/core/styles';

const themeColorsDefault = {
    back : {
        default: lighten(teal[100], 0.8),
        inverse: darken(teal[900], 0.8),
        paper: lightBlue[50],
        input: grey[50],
        inputActiv: blueGrey[100],
        inputHover: grey[200],
        button: grey[50],
        buttonHover: grey[50],
        navbar: blue[700],
    },

    front: {
        default : grey[900],
        text: grey[900],
        button: grey[900],
        buttonHover: blue[700],
        header: grey[900],
        label: blue[700],
        labelLight: blue[300],
        navbar: lighten(lightBlue[50], 0.9),
    },

    shadow: {
        default: blue[700],
        light: grey[300],
        main: grey[600],
        dark: grey[900],
    },

    error : {
        light: red[300],
        main: red[500],
        dark: red[700],
    },

    typography: {
        fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
        fontSize: '1em',       // Basisschriftgröße
        fontSizeBig: '1.3em',       // vergrößerte Schriftgröße
        fontSizeSmall: '0.8em',       // verkleinerte Schriftgröße
        fontWeightLight: 300,
        fontWeightRegular: 400,
        fontWeightMedium: 500,
        fontWeightBold: 700,
      
    },
}



export const themeColors = themeColorsDefault
