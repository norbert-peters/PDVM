import styled from 'styled-components'
import { Grid } from '../pdvmComponents/PdvmRaster';


export const PdvmPaper = styled(Grid)`
${({ theme }) => `
  color: ${theme.primaryLight}} ;
  background-color: ${theme.palette.text.secondary} ;
  padding: 0.3em 0.7em ;
  box-shadow: 5px 5px 3px #888888;
  margin-bottom: 0.5em;
​​  `}
`;
