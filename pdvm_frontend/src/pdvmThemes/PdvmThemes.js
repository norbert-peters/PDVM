import { createMuiTheme } from 'material-ui/styles';

import blue from 'material-ui/colors/blue';

const baseTheme = createMuiTheme({
    palette: {
        primary: {
            c100: blue[100],
            c200: blue[200],
            light: blue[300],
            main: blue[500],
            dark: blue[700]
        }
    },
    typography: {
        fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
        fontSize: 14,
        fontWeightLight: 300,
        fontWeightRegular: 400,
        fontWeightMedium: 500,
        fontWeightBold: 700
    },
    anchor: {
        main: blue[500],
        selected: blue[700]
    },
    text: {
        home: '#fff',
        main: '#3f5742'
    },
    button: {
    // Schriftfarbe Normal
        colorNormaly: 'black',
        colorAttention: 'red',
        colorGreen: 'green',
        colorRed: 'orange',
        colorDefault: 'black',
    // Schriftfarbe bei hover
        colorHoverNormaly: 'yellow',
        colorHoverAttention: 'orange',
        colorHoverGreen: 'black',
        colorHoverRed: 'red',
        colorHoverDefault: 'yellow',
    // Schriftfarbe bei focus -- focus nicht anzeigen, Farbe wie Normal
        colorFocusNormaly: 'black',
        colorFocusAttention: 'black',
        colorFocusGreen: 'black',
        colorFocusRed: 'black',
        colorFocusDefault: 'black',
    // Hintergrundfarbe Normal
        BackColorNormaly: blue[500],
        BackColorAttention: 'orange',
        BackColorGreen: '#fff',
        BackColorRed: '#fff',
        BackColorDefault: '#fff',
    // Hintergrundfarbe bei hover
        BackColorHoverNormaly: blue[100],
        BackColorHoverAttention: 'green',
        BackColorHoverGreen: 'red',
        BackColorHoverRed: 'lightblue',
        BackColorHoverDefault: 'grey',
    // Hintergrundfarbe bei focus - focus nicht anzeigen, Farbe wie Normal
        BackColorFocusNormaly: '#aaa',
        BackColorFocusAttention: '#aaa',
        BackColorFocusGreen: '#aaa',
        BackColorFocusRed: '#aaa',
        BackColorFocusDefault: '#aaa',
    // Rahmen Stärke/Farbe Normal
        borderNormaly: '2px solid black',
        borderAttention: '2px solid red',
        borderGreen: '2px solid green',
        borderRed: '2px solid orange',
        borderDefault: '2px solid black',    
    // Rahmen Stärke/Farbe bei hover
        borderHoverNormaly: '2px solid magenta',
        borderHoverAttention: '2px solid magenta',
        borderHoverGreen: '2px solid magenta',
        borderHoverRed: '2px solid magenta',
        borderHoverDefault: '2px solid magenta',    
    // Rahmen Stärke/Farbe bei focus
        borderFocusNormaly: '2px solid lightblue',
        borderFocusAttention: '2px solid lightblue',
        borderFocusGreen: '2px solid lightblue',
        borderFocusRed: '2px solid lightblue',
        borderFocusDefault: '2px solid lightblue',    

    }
});

export { baseTheme as pdvmTheme };