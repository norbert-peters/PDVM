import { createMuiTheme } from '@material-ui/core/styles';
import blue from 'material-ui/colors/blue';
import { orange } from '@material-ui/core/colors';


export const PdvmLightTheme = createMuiTheme({
    overrides: {
        MuiOutlinedInput: {
            root:{
                color: 'black',
                background: blue[100],

            }
        },
    },
    palette: {
        primary: {
            light: blue[100],
            main: blue[500],
            dark: blue[900]
        },
        secondary: {
            light: orange[100],
            main: orange[500],
            dark: orange[900]
        },
        type: 'light',
        text: {
            label: "rgba(0, 0, 0, 0.87)",
            disabled: "rgba(255, 255, 255, 0.5)",
            hint: "rgba(255, 255, 255, 0.5)",
            icon: "rgba(255, 255, 255, 0.5)",
            primary: "#000",
            secondary: "rgba(255, 255, 255, 0.7)" ,
        },
    },
    typography: {
        fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
        fontSize: 14,
        fontWeightLight: 300,
        fontWeightRegular: 400,
        fontWeightMedium: 500,
        fontWeightBold: 700
    },
})
