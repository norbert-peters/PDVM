import styled from 'styled-components'
import { Grid } from '../pdvmComponents/PdvmRaster';


export const PdvmPaper = styled(Grid)`
${({ theme }) => `
  color: ${theme.front.text}} ;
  background-color: ${theme.back.paper} ;
  padding: 0.3em 0.7em ;
  box-shadow: 3px 3px 1px ${theme.shadow.default};
  margin-bottom: 0.5em;
​​  `}
`;
